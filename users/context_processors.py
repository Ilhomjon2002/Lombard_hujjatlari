from .models import Branch

def sidebar_branches(request):
    branches = Branch.objects.all()
    return {
        'sidebar_branches': branches
    }
