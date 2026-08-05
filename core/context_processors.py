def user_preferences(request):
    theme_preference = 'system'
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.theme_preference:
            theme_preference = profile.theme_preference

    return {
        'user_theme_preference': theme_preference,
    }