class FlowSelectors:
    """Centralized resilient selectors for Google Flow UI automation with ARIA fallbacks."""

    # Navigation & Authentication
    LANDING_ENTRY = (
        "button:has-text('Create with Google Flow'), "
        "button:has-text('Try Google Flow'), "
        "a:has-text('Sign in')"
    )
    NEW_PROJECT_BTN = (
        "button:has-text('New project'), "
        "button:has-text('+ New project'), "
        "[aria-label='New project']"
    )
    PROJECT_CARDS = "flow-project-card, a[href*='/project/'], .project-card"
    PROJECT_TITLE = ".project-title, header h1, [aria-label*='project title' i]"

    # Transient Onboarding Dialogs & Gallery Banners
    HERO_START_CREATING = (
        "button:has-text('Start Creating'), "
        "[aria-label*='Start creating' i]"
    )
    HERO_CLOSE_BTN = (
        "button[aria-label*='close' i], "
        "[aria-label*='dismiss' i]"
    )
    DISMISS_MODALS = (
        "button:has-text('Got it'), "
        "button:has-text('Got It'), "
        "button:has-text('Dismiss'), "
        "button:has-text('I understand'), "
        "[role='dialog'] button[aria-label*='close' i]"
    )

    # Studio Workspace & Prompt Bar
    PROMPT_INPUT = ".ProseMirror, div[contenteditable='true'], textarea[aria-label*='prompt' i]"
    GENERATE_BTN = (
        "button[aria-label='Start generation'], "
        "button[aria-label='Generate'], "
        "flow-generate-icon-button button, "
        "button:has-text('Generate')"
    )
    GENERATION_ACTIVE_INDICATOR = (
        "button[aria-label='Stop generation'], "
        "flow-generate-icon-button button.generating, "
        ".generating-indicator"
    )
    STOP_GENERATION_BTN = (
        "button[aria-label='Stop generation'], "
        "button:has-text('Stop generation'), "
        "button:has-text('Stop')"
    )

    # Model & Parameter Selectors in Prompt Bar
    MODEL_SELECTOR_PILL = (
        "flow-model-select button, "
        "[aria-label*='model' i], "
        "button:has-text('Banana'), "
        "button:has-text('Veo'), "
        "button:has-text('Gemini'), "
        ".model-selector-pill"
    )
    MODEL_MENU_OPTIONS = (
        "[role='menuitem'], "
        "[role='option'], "
        ".mat-mdc-menu-item, "
        "flow-select-option, "
        "[role='listbox'] > *"
    )
    ASPECT_RATIO_PILL = (
        "button:has-text('16:9'), "
        "button:has-text('9:16'), "
        "button:has-text('1:1'), "
        "[aria-label*='aspect' i]"
    )
    OUTPUT_COUNT_PILL = (
        "button:has-text('x1'), "
        "button:has-text('x2'), "
        "button:has-text('x4'), "
        "[aria-label*='output count' i]"
    )

    # Confirmation & Safety Prompts
    APPROVAL_PROMPT_CONTAINER = "[role='alert'], .flow-chat-bubble, [role='dialog'], .mat-mdc-dialog-container"
    ALWAYS_APPROVE_BTN = (
        "button:has-text('Always approve'), "
        "[role='button']:has-text('Always approve')"
    )
    APPROVE_BTN = (
        "button:has-text('Approve'), "
        "[role='button']:has-text('Approve'), "
        "button:has-text('Generate anyway'), "
        "button:has-text('Confirm')"
    )
    REJECT_BTN = (
        "button:has-text('Reject'), "
        "button:has-text('Cancel')"
    )

    # Canvas Media & Video Tiles
    VIDEO_TILE = "flow-video-tile, [data-tile-type='video']"
    TILE_CONTAINER = "flow-tile-container, flow-grid-tile-container"
    TILE_HOTBAR = "flow-video-hotbar, flow-hotbar-container, .tile-hotbar"
    TILE_MORE_OPTIONS = "flow-video-hotbar button[aria-label*='options' i], button[aria-label*='More' i]"
    TILE_PROGRESS_BAR = ".progress-bar, [role='progressbar'], flow-progress-bar"
    TILE_THUMBNAIL = "flow-video-tile img.thumbnail, flow-video-tile img"
    TILE_TITLE = "flow-tile-hover-footer .footer-title, .tile-title, [class*='footer-title']"
    PLAY_CIRCLE_ICON = (
        "mat-icon:has-text('play_circle'), "
        "[data-mat-icon-type]:has-text('play_circle'), "
        ".type-icon-container mat-icon"
    )

    # Download & Export
    DOWNLOAD_BUTTONS = (
        "button:has-text('Download'), "
        "button[aria-label*='Download' i], "
        "[role='menuitem']:has-text('Download'), "
        "[data-tooltip*='Download' i]"
    )
    DOWNLOAD_QUALITY_OPTIONS = (
        "[role='menuitem']:has-text('720p'), "
        "[role='menuitem']:has-text('1080p'), "
        "[role='menuitem']:has-text('Original size'), "
        "button:has-text('720p'), "
        "button:has-text('1080p'), "
        ":text-matches('720p', 'i')"
    )
    EXPORT_BUTTONS = (
        "button:has-text('Export'), "
        "button[aria-label*='Export' i]"
    )

    # Credit & Account Inspection
    USER_AVATAR = (
        "flow-header-user-icon, "
        "button[aria-label*='Google Account' i], "
        ".flow-user-tier-chip"
    )
    CREDIT_CONTAINER = (
        ".flow-credit-banner, "
        "[aria-label*='credits' i], "
        ":text-matches('Google Flow credits')"
    )
