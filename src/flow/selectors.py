class FlowSelectors:
    """Centralized selectors for Google Flow UI automation."""

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

    # Studio Workspace & Prompting
    PROMPT_INPUT = ".ProseMirror, div[contenteditable='true']"
    GENERATE_BTN = (
        "button[aria-label='Start generation'], "
        "button[aria-label='Generate'], "
        "flow-generate-icon-button button"
    )
    GENERATION_ACTIVE_INDICATOR = (
        "button[aria-label='Stop generation'], "
        "flow-generate-icon-button button.generating"
    )

    # Confirmation & Safety Prompts
    APPROVAL_PROMPT_CONTAINER = "[role='alert'], .flow-chat-bubble, [role='dialog']"
    ALWAYS_APPROVE_BTN = (
        "button:has-text('Always approve'), "
        "[role='button']:has-text('Always approve')"
    )
    APPROVE_BTN = (
        "button:has-text('Approve'), "
        "[role='button']:has-text('Approve')"
    )
    REJECT_BTN = "button:has-text('Reject')"

    # Canvas Media & Video Tiles
    VIDEO_TILE = "flow-video-tile"
    TILE_CONTAINER = "flow-tile-container, flow-grid-tile-container"
    TILE_HOTBAR = "flow-video-hotbar, flow-hotbar-container"
    TILE_MORE_OPTIONS = "flow-video-hotbar button[aria-label='More options']"
    TILE_PROGRESS_BAR = ".progress-bar"
    TILE_THUMBNAIL = "flow-video-tile img.thumbnail"
    TILE_TITLE = "flow-tile-hover-footer .footer-title"

    # Download & Export
    DOWNLOAD_BUTTONS = (
        "button:has-text('Download'), "
        "button[aria-label*='Download' i], "
        "[role='menuitem']:has-text('Download'), "
        "[data-tooltip*='Download' i]"
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
