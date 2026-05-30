"""
Main Window - Universal Host GUI
Integrasi semua komponen UI menjadi aplikasi utama yang kohesif
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MainWindow:
    """
    Main window aplikasi Universal Host.
    Mengintegrasikan:
    - Sistem tab multi-aplikasi
    - Accordion search untuk launch aplikasi
    - Loading overlay
    - Log panel (F2 toggle)
    - Toolbar dengan Repair, Close All, Reset Workspace
    """
    
    def __init__(self):
        self.tab_manager = None
        self.embedder = None
        self.launcher = None
        self.log_panel = None
        self.loading_overlay = None
        self.search_component = None
        
        self.initialized = False
        
    def initialize(self, tab_manager, embedder, launcher, 
                   log_panel, loading_overlay, search_component) -> bool:
        """
        Menginisialisasi main window dengan semua komponen
        
        Args:
            tab_manager: TabManager instance
            embedder: EmbeddingManager instance
            launcher: ApplicationLauncher instance
            log_panel: LogPanel instance
            loading_overlay: LoadingOverlay instance
            search_component: AccordionAutocomplete instance
            
        Returns:
            True jika berhasil
        """
        try:
            self.tab_manager = tab_manager
            self.embedder = embedder
            self.launcher = launcher
            self.log_panel = log_panel
            self.loading_overlay = loading_overlay
            self.search_component = search_component
            
            self.initialized = True
            logger.info("MainWindow initialized with all components")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize MainWindow: {e}")
            return False
    
    def launch_and_embed(self, app_path: str) -> bool:
        """
        Launch aplikasi dan embed ke tab baru
        
        Args:
            app_path: Path ke aplikasi
            
        Returns:
            True jika berhasil
        """
        if not self.initialized:
            logger.error("MainWindow not initialized")
            return False
        
        # Show loading overlay
        self.loading_overlay.show("Launching application...", 0)
        
        try:
            # Step 1: Launch aplikasi
            result = self.launcher.launch(app_path)
            
            if not result.success:
                logger.error(f"Failed to launch: {result.error}")
                self.loading_overlay.hide()
                return False
            
            self.loading_overlay.update_progress(30)
            
            # Step 2: Buat tab baru
            app_name = result.path.split('\\')[-1] if '\\' in result.path else result.path.split('/')[-1]
            tab_id = self.tab_manager.create_tab(
                title=f"Loading {app_name}...",
                process_name=app_name,
                pid=result.pid
            )
            
            self.loading_overlay.update_progress(60)
            
            # Step 3: Embed window ke tab
            session = self.embedder.create_embedding(
                pid=result.pid,
                app_name=app_name,
                app_path=result.path,
                tab_id=tab_id
            )
            
            if session:
                self.loading_overlay.update_progress(90)
                
                # Update tab title dengan nama proses actual
                self.tab_manager.update_tab_title(tab_id, app_name)
                
                self.loading_overlay.update_progress(100)
                logger.info(f"Successfully launched and embedded: {app_name}")
            else:
                logger.warning("Embedding failed, but app is running")
            
            # Hide loading overlay setelah delay singkat
            self.loading_overlay.hide()
            return True
            
        except Exception as e:
            logger.error(f"Error in launch_and_embed: {e}")
            self.loading_overlay.hide()
            return False
    
    def close_current_tab(self) -> bool:
        """Menutup tab yang sedang aktif"""
        if not self.initialized:
            return False
        
        active_tab = self.tab_manager.get_active_tab()
        if active_tab:
            return self.tab_manager.remove_tab(active_tab.tab_id)
        
        return False
    
    def close_all_tabs(self) -> int:
        """Menutup semua tab"""
        if not self.initialized:
            return 0
        
        # Cleanup embedding sessions dulu
        self.embedder.cleanup_all()
        
        # Tutup semua tab
        count = self.tab_manager.close_all_tabs(force=True)
        logger.info(f"Closed all tabs: {count}")
        return count
    
    def toggle_log_panel(self) -> bool:
        """Toggle visibilitas log panel (F2 shortcut)"""
        if not self.initialized or not self.log_panel:
            return False
        
        return self.log_panel.toggle_visibility()
    
    def reset_workspace(self) -> bool:
        """
        Reset workspace ke default layout
        Menutup semua tab dan clear state
        """
        logger.info("Resetting workspace...")
        
        # Close all tabs
        self.close_all_tabs()
        
        # Clear log panel
        if self.log_panel:
            self.log_panel.clear()
        
        # Reset search component
        if self.search_component:
            self.search_component.collapse()
        
        logger.info("Workspace reset complete")
        return True
    
    def repair_application(self, app_path: str) -> bool:
        """
        Buka Control Panel untuk repair aplikasi
        
        Args:
            app_path: Path aplikasi yang ingin di-repair
            
        Returns:
            True jika berhasil membuka Control Panel
        """
        logger.info(f"Opening Control Panel for repair: {app_path}")
        
        # Di Windows, buka Control Panel atau Settings
        # Implementasi akan menggunakan subprocess untuk membuka control panel
        
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Mendapatkan status aplikasi
        
        Returns:
            Dict dengan status lengkap
        """
        return {
            'initialized': self.initialized,
            'active_tabs': self.tab_manager.get_tab_count() if self.tab_manager else 0,
            'log_visible': self.log_panel.is_visible if self.log_panel else False,
            'loading_visible': self.loading_overlay.is_showing() if self.loading_overlay else False,
            'embedded_sessions': len(self.embedder.sessions) if self.embedder else 0
        }


# Helper function
def get_main_window() -> MainWindow:
    """Mendapatkan instance MainWindow"""
    return MainWindow()
