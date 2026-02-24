# Scanner fingerprint authentication views
# Add these to your users/views.py

import json
import requests
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.timezone import now
from .models import CustomUser, ScannerFingerprintTemplate

logger = logging.getLogger(__name__)

# Local agent configuration
AGENT_HOST = '127.0.0.1'
AGENT_PORT = 8001
AGENT_BASE_URL = f'http://{AGENT_HOST}:{AGENT_PORT}'


def check_agent_health():
    """Check if local agent is running"""
    try:
        response = requests.get(
            f'{AGENT_BASE_URL}/api/status',
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


@require_http_methods(["GET"])
def scanner_status(request):
    """Get fingerprint scanner status"""
    try:
        # Check if agent is running
        if not check_agent_health():
            return JsonResponse({
                'success': False,
                'agent_running': False,
                'message': 'Local agent is not running'
            }, status=503)
        
        # Get scanner status from agent
        response = requests.get(
            f'{AGENT_BASE_URL}/api/scanner/detect',
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return JsonResponse({
                'success': True,
                'agent_running': True,
                'scanner_detected': data.get('success', False),
                'scanner_status': data.get('status', {}),
                'message': data.get('message', '')
            })
        else:
            return JsonResponse({
                'success': False,
                'agent_running': True,
                'scanner_detected': False,
                'message': 'Scanner not detected'
            }, status=404)
            
    except requests.ConnectionError:
        logger.error('Failed to connect to local agent')
        return JsonResponse({
            'success': False,
            'agent_running': False,
            'message': 'Cannot connect to fingerprint agent. Please ensure it is running.'
        }, status=503)
    except Exception as e:
        logger.error(f'Scanner status error: {e}')
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def fingerprint_register_start(request):
    """Start fingerprint registration"""
    try:
        # Check if user already has registered fingerprint
        if hasattr(request.user, 'scanner_fingerprint') and request.user.scanner_fingerprint:
            return JsonResponse({
                'success': False,
                'error': 'User already has a registered fingerprint. Remove it first.'
            }, status=400)
        
        # Check agent health
        if not check_agent_health():
            return JsonResponse({
                'success': False,
                'error': 'Fingerprint agent is not running'
            }, status=503)
        
        # Start capture on agent
        response = requests.post(
            f'{AGENT_BASE_URL}/api/fingerprint/start-capture',
            timeout=5
        )
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Failed to start fingerprint capture'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'Fingerprint capture started. Please place your finger on the scanner.',
            'session': response.json().get('session', {})
        })
        
    except requests.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint agent is not responding'
        }, status=503)
    except Exception as e:
        logger.error(f'Register start error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["GET"])
def fingerprint_capture(request):
    """Capture fingerprint from local agent"""
    try:
        # Call agent to capture fingerprint
        response = requests.get(
            f'{AGENT_BASE_URL}/api/fingerprint/capture',
            timeout=15
        )
        
        if response.status_code != 200:
            data = response.json()
            return JsonResponse({
                'success': False,
                'error': data.get('error', 'Fingerprint capture failed'),
                'quality': data.get('quality', 0)
            }, status=400)
        
        data = response.json()
        
        # Check quality score
        quality = data.get('quality', 0)
        if quality < 50:
            return JsonResponse({
                'success': False,
                'error': f'Fingerprint quality too low ({quality}/100). Please try again.',
                'quality': quality
            }, status=400)
        
        # Store template data in session for registration completion
        request.session['fingerprint_template'] = data.get('template')
        request.session['fingerprint_quality'] = quality
        
        return JsonResponse({
            'success': True,
            'message': 'Fingerprint captured successfully',
            'quality': quality,
            'template_stored': True
        })
        
    except requests.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint capture timeout. Please try again.'
        }, status=408)
    except requests.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint agent is not responding'
        }, status=503)
    except Exception as e:
        logger.error(f'Capture error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def fingerprint_register_complete(request):
    """Complete fingerprint registration"""
    try:
        # Get template from session
        template = request.session.get('fingerprint_template')
        quality = request.session.get('fingerprint_quality', 0)
        
        if not template:
            return JsonResponse({
                'success': False,
                'error': 'No fingerprint captured. Please capture your fingerprint first.'
            }, status=400)
        
        # Get finger position from request
        data = json.loads(request.body)
        finger_position = data.get('finger_position', 'right_index')
        
        # Create or update scanner fingerprint template
        fingerprint, created = ScannerFingerprintTemplate.objects.update_or_create(
            user=request.user,
            defaults={
                'template_data': template.encode(),
                'quality_score': quality,
                'finger_position': finger_position,
                'is_registered': True,
                'algorithm': 'ZKTECO_MINEX'
            }
        )
        
        # Clear session
        request.session.pop('fingerprint_template', None)
        request.session.pop('fingerprint_quality', None)
        
        messages.success(request, 'Fingerprint registered successfully!')
        
        return JsonResponse({
            'success': True,
            'message': 'Fingerprint registered successfully',
            'redirect': '/profile/'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except Exception as e:
        logger.error(f'Register complete error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def fingerprint_authenticate(request):
    """Authenticate user with fingerprint"""
    try:
        # Get username from request
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            }, status=400)
        
        # Find user
        try:
            user = CustomUser.objects.get(username__iexact=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Check if user has fingerprint registered
        if not hasattr(user, 'scanner_fingerprint') or not user.scanner_fingerprint:
            return JsonResponse({
                'success': False,
                'error': 'User does not have fingerprint authentication enabled'
            }, status=400)
        
        if not user.scanner_fingerprint.is_registered:
            return JsonResponse({
                'success': False,
                'error': 'Fingerprint is not activated'
            }, status=400)
        
        # Start capture on agent
        response = requests.post(
            f'{AGENT_BASE_URL}/api/fingerprint/start-capture',
            timeout=5
        )
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Failed to start fingerprint capture on scanner'
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'message': 'Scanner ready. Please place your finger on the scanner.',
            'username': username
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except requests.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint agent is not responding'
        }, status=503)
    except Exception as e:
        logger.error(f'Auth start error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["POST"])
def fingerprint_verify(request):
    """Verify fingerprint for authentication"""
    try:
        from django.contrib.auth import login
        
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            }, status=400)
        
        # Find user
        try:
            user = CustomUser.objects.get(username__iexact=username)
        except CustomUser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'User not found'
            }, status=404)
        
        # Get captured fingerprint from agent
        response = requests.get(
            f'{AGENT_BASE_URL}/api/fingerprint/capture',
            timeout=15
        )
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Fingerprint capture failed. Please try again.'
            }, status=400)
        
        current_template = response.json().get('template')
        quality = response.json().get('quality', 0)
        
        if quality < 50:
            return JsonResponse({
                'success': False,
                'error': f'Fingerprint quality too low ({quality}/100). Please try again.',
                'quality': quality
            }, status=400)
        
        # Get stored fingerprint template
        stored_fingerprint = user.scanner_fingerprint
        stored_template = stored_fingerprint.template_data.decode()
        
        # Verify with agent
        verify_response = requests.post(
            f'{AGENT_BASE_URL}/api/fingerprint/verify',
            json={
                'stored_template': stored_template,
                'current_template': current_template,
                'threshold': 90
            },
            timeout=5
        )
        
        if verify_response.status_code != 200:
            return JsonResponse({
                'success': False,
                'error': 'Fingerprint verification failed'
            }, status=500)
        
        verify_data = verify_response.json()
        
        if not verify_data.get('match'):
            similarity = verify_data.get('similarity_score', 0)
            return JsonResponse({
                'success': False,
                'error': f'Fingerprint does not match. Similarity: {similarity}%',
                'similarity': similarity
            }, status=401)
        
        # Authentication successful - log user in
        login(request, user)
        
        # Update verification stats
        stored_fingerprint.last_verified = now()
        stored_fingerprint.verification_count += 1
        stored_fingerprint.save()
        
        logger.info(f'User {user.username} authenticated with fingerprint')
        
        return JsonResponse({
            'success': True,
            'message': 'Authentication successful',
            'redirect': '/dashboard/',
            'similarity': verify_data.get('similarity_score', 100)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        }, status=400)
    except requests.Timeout:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint verification timeout'
        }, status=408)
    except requests.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'Fingerprint agent is not responding'
        }, status=503)
    except Exception as e:
        logger.error(f'Verify error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def fingerprint_remove(request):
    """Remove fingerprint registration"""
    try:
        if hasattr(request.user, 'scanner_fingerprint') and request.user.scanner_fingerprint:
            request.user.scanner_fingerprint.delete()
            messages.success(request, 'Fingerprint authentication removed successfully')
            return JsonResponse({'success': True, 'message': 'Fingerprint removed'})
        
        return JsonResponse({
            'success': False,
            'error': 'No fingerprint registration found'
        }, status=404)
        
    except Exception as e:
        logger.error(f'Remove fingerprint error: {e}')
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
