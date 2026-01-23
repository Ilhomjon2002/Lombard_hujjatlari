from .models import Branch

def sidebar_branches(request):
    branches = Branch.objects.select_related('parent_branch').prefetch_related('sub_branches')
    return {
        'sidebar_branches': branches
    }
