"""
Main Entry Point - Universal Host Application
"""
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point untuk Universal Host"""
    logger.info("Universal Host starting...")
    
    # Import core components
    from core.engine import get_engine
    from core.window_manager import get_window_manager
    from modules.launcher import get_launcher
    from modules.embedder import get_embedder
    from modules.tab_manager import get_tab_manager
    from ui.components.loading_overlay import get_loading_overlay
    from ui.components.accordion_search import get_autocomplete
    from ui.components.log_panel import get_log_panel
    from ui.main_window import get_main_window
    
    # Initialize core engine
    engine = get_engine()
    logger.info("Core Engine initialized")
    
    # Initialize window manager
    window_manager = get_window_manager()
    logger.info("Window Manager initialized")
    
    # Initialize launcher
    launcher = get_launcher()
    logger.info("Application Launcher initialized")
    
    # Initialize embedder
    embedder = get_embedder(window_manager)
    logger.info("Embedding Manager initialized")
    
    # Initialize tab manager
    tab_manager = get_tab_manager()
    logger.info("Tab Manager initialized")
    
    # Initialize UI components
    loading_overlay = get_loading_overlay()
    autocomplete = get_autocomplete()
    log_panel = get_log_panel()
    logger.info("UI Components initialized")
    
    # Initialize main window
    main_window = get_main_window()
    main_window.initialize(
        tab_manager=tab_manager,
        embedder=embedder,
        launcher=launcher,
        log_panel=log_panel,
        loading_overlay=loading_overlay,
        search_component=autocomplete
    )
    logger.info("MainWindow initialized")
    
    # Demo: Add some sample applications to search
    autocomplete.add_item("Notepad", "notepad.exe", category="System")
    autocomplete.add_item("Calculator", "calc.exe", category="System")
    
    logger.info("Universal Host ready!")
    logger.info(f"Status: {main_window.get_status()}")
    
    # Dalam implementasi actual, di sini akan masuk ke Qt event loop
    # app = QApplication(sys.argv)
    # window = MainWindowQt()  # PyQt6 implementation
    # window.show()
    # sys.exit(app.exec())
    
    print("\n" + "="*60)
    print("UNIVERSAL HOST - Ready for Launch")
    print("="*60)
    print("Components loaded:")
    print(f"  - Core Engine: OK")
    print(f"  - Window Manager: OK ({'Win32' if window_manager._win32_available else 'Mock'} mode)")
    print(f"  - Launcher: OK")
    print(f"  - Embedder: OK")
    print(f"  - Tab Manager: OK")
    print(f"  - UI Components: OK")
    print("="*60)
    print("\nTo run the full GUI application:")
    print("  1. Install PyQt6: pip install PyQt6")
    print("  2. Run on Windows for full Win32 API support")
    print("  3. Execute: python main.py")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
