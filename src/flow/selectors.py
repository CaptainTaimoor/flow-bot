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
    SETTINGS_TRIGGER_BTN = (
        "button[aria-label='Settings trigger'], "
        ".settings-trigger-button, "
        "flow-creative-agent-prompt-box button.settings-trigger-button, "
        "button:has-text('Banana'), "
        "button:has-text('Veo'), "
        "button:has-text('Video'), "
        "button:has-text('x1')"
    )
    AGENT_MODE_CHIP = ".agent-mode-chip, button:has-text('Agent')"
    VIDEO_TAB_TOGGLE = "mat-button-toggle:has-text('Video'), button:has-text('Video')"
    IMAGE_TAB_TOGGLE = "mat-button-toggle:has-text('Image'), button:has-text('Image')"
    SELECT_MODEL_FAMILY_BTN = "button[aria-label='Select model family']"
    PANEL_CLOSE_BTN = "button[aria-label='Close'], button:has-text('close')"
    RESOLUTION_DOWNLOAD_BTN = (
        ".cdk-overlay-pane button[role='menuitem']:has-text('Original size'), "
        ".cdk-overlay-pane button[role='menuitem']:has-text('720p'), "
        ".cdk-overlay-pane button[role='menuitem']:has-text('1080p'), "
        "button[role='menuitem']:has-text('Original size')"
    )

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
        ".cdk-overlay-pane button[role='menuitem']:has-text('Original size'), "
        ".cdk-overlay-pane button[role='menuitem']:has-text('720p'), "
        ".cdk-overlay-pane button[role='menuitem']:has-text('1080p'), "
        "[role='menuitem']:has-text('Original size'), "
        "[role='menuitem']:has-text('720p'), "
        "[role='menuitem']:has-text('1080p')"
    )
    EXPORT_BUTTONS = (
        "button:has-text('Export'), "
        "button[aria-label*='Export' i]"
    )

    # Agent Settings Panel
    SETTINGS_BTN = (
        "button[aria-label='Settings'], "
        "flow-creative-agent-prompt-box button:has-text('tune'), "
        "button:has-text('tune')"
    )
    AGENT_PANEL = "flow-agent-panel"
    VIDEO_MODEL_PICKER = (
        "button[aria-label='Video generation default model'], "
        ".video-model-picker-button"
    )
    VIDEO_MODEL_MENU_ITEMS = (
        "[role='menu'] [role='menuitem'], "
        ".flow-model-picker-panel [role='menuitem'], "
        ".model-picker-panel [role='menuitem']"
    )
    SETTINGS_SAVE_BTN = (
        "button.settings-save-button, "
        "flow-agent-panel button:has-text('Save')"
    )
    CONFIRM_NEVER_RADIO = (
        "flow-agent-panel mat-radio-button:has-text('Never'), "
        "flow-agent-panel [role='radio']:has-text('Never')"
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
    ACCOUNT_DETAILS_BTN = (
        "[aria-label='Account details'], "
        ".header-user-button, "
        "flow-header-user-icon div[role='button']"
    )
    ACCOUNT_DIALOG = (
        "div[role='dialog'].panel, "
        ".flow-account-panel-overlay, "
        ".panel"
    )
    ACCOUNT_CLOSE_BTN = (
        ".flow-account-panel-overlay button[aria-label='Close'], "
        ".panel button:has-text('close'), "
        ".panel mat-icon:has-text('close')"
    )
