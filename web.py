import sys
import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import *
import shutil
from pathlib import Path

# Скрываем консоль Windows
if sys.platform == 'win32':
    import win32gui
    import win32con
    # Скрываем консоль
    hwnd = win32gui.GetForegroundWindow()
    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)

# Создаем папку для загрузок, если её нет
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'WebBrowser')
if not os.path.exists(downloads_path):
    os.makedirs(downloads_path)

class DownloadWidget(QWidget):
    def __init__(self, download, parent=None):
        super().__init__(parent)
        self.download = download
        self.download_path = download.path()
        self.is_paused = False
        
        layout = QHBoxLayout()
        
        # Информация о файле
        info_layout = QVBoxLayout()
        
        # Название файла
        self.filename_label = QLabel(os.path.basename(self.download_path))
        self.filename_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.filename_label)
        
        # Путь к файлу
        self.path_label = QLabel(os.path.dirname(self.download_path))
        self.path_label.setStyleSheet("color: gray;")
        info_layout.addWidget(self.path_label)
        
        layout.addLayout(info_layout)
        
        # Размер и прогресс
        progress_layout = QVBoxLayout()
        
        # Размер файла
        self.size_label = QLabel()
        progress_layout.addWidget(self.size_label)
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(200)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addLayout(progress_layout)
        
        # Скорость загрузки
        self.speed_label = QLabel()
        layout.addWidget(self.speed_label)
        
        # Добавляем кнопки управления
        control_layout = QHBoxLayout()
        
        # Кнопка паузы/возобновления
        self.pause_btn = QPushButton()
        self.pause_btn.setFixedSize(32, 32)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 16px;
                background: #f0f0f0;
                color: #333333;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
            QPushButton:pressed {
                background: #d0d0d0;
            }
        """)
        self.pause_btn.setText("⏸")
        self.pause_btn.setToolTip("Пауза")
        self.pause_btn.clicked.connect(self.toggle_pause)
        control_layout.addWidget(self.pause_btn)
        
        # Кнопка отмены
        self.cancel_btn = QPushButton()
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 16px;
                background: #f0f0f0;
                color: #333333;
            }
            QPushButton:hover {
                background: #ffebee;
                color: #d32f2f;
            }
            QPushButton:pressed {
                background: #ffcdd2;
            }
        """)
        self.cancel_btn.setText("✕")
        self.cancel_btn.setToolTip("Отменить")
        self.cancel_btn.clicked.connect(self.cancel_download)
        control_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(control_layout)
        self.setLayout(layout)
        
        # Подключаем сигналы загрузки
        self.download.downloadProgress.connect(self.update_progress)
        self.download.finished.connect(self.download_finished)
        self.download.stateChanged.connect(self.state_changed)
        
    def toggle_pause(self):
        if self.is_paused:
            self.download.resume()
            self.pause_btn.setText("⏸")
            self.pause_btn.setToolTip("Пауза")
            self.is_paused = False
            self.speed_label.setText("Возобновлено")
        else:
            self.download.pause()
            self.pause_btn.setText("▶")
            self.pause_btn.setToolTip("Продолжить")
            self.is_paused = True
            self.speed_label.setText("Приостановлено")
    
    def cancel_download(self):
        reply = QMessageBox.question(
            self,
            'Подтверждение',
            'Вы уверены, что хотите отменить загрузку?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download.cancel()
            self.speed_label.setText("Отменено")
            self.progress_bar.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
    
    def state_changed(self, state):
        if state == QWebEngineDownloadItem.DownloadCompleted:
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.speed_label.setText("Завершено")
        elif state == QWebEngineDownloadItem.DownloadCancelled:
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            self.speed_label.setText("Отменено")
        elif state == QWebEngineDownloadItem.DownloadInterrupted:
            self.speed_label.setText("Прервано")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            
    def update_progress(self, bytes_received, bytes_total):
        try:
            # Обновляем прогресс
            self.progress_bar.setMaximum(bytes_total)
            self.progress_bar.setValue(bytes_received)
            
            # Обновляем размер
            total_mb = bytes_total / (1024 * 1024)
            received_mb = bytes_received / (1024 * 1024)
            self.size_label.setText(f"{received_mb:.1f} MB / {total_mb:.1f} MB")
            
            # Вычисляем и показываем скорость если загрузка не на паузе
            if not self.is_paused:
                speed = bytes_received / max(1, self.download.elapsedTime().elapsed() / 1000.0)
                speed_mb = speed / (1024 * 1024)
                self.speed_label.setText(f"{speed_mb:.1f} MB/s")
            
        except Exception as e:
            print(f"Ошибка при обновлении прогресса: {str(e)}")
            
    def download_finished(self):
        try:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.speed_label.setText("Завершено")
            self.pause_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
        except Exception as e:
            print(f"Ошибка при завершении загрузки: {str(e)}")

class DownloadsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузки")
        self.setGeometry(200, 200, 600, 400)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        layout = QVBoxLayout(central_widget)
        
        # Область прокрутки для загрузок
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Контейнер для загрузок
        self.downloads_container = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_container)
        self.downloads_layout.addStretch()
        
        scroll.setWidget(self.downloads_container)
        
    def add_download(self, download_widget):
        self.downloads_layout.insertWidget(self.downloads_layout.count()-1, download_widget)
        self.show()
        self.raise_()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Web Browser')
        self.setGeometry(100, 100, 1200, 800)
        
        # Современный стиль для всего браузера
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            
            /* Стиль вкладок */
            QTabWidget::pane {
                border: none;
                background: #ffffff;
                margin-top: -1px;
            }
            QTabBar::tab {
                background: transparent;
                border: none;
                padding: 8px 30px;
                margin-right: 2px;
                color: #5f6368;
                font-size: 13px;
                min-width: 120px;
                max-width: 200px;
            }
            QTabBar::tab:selected {
                color: #1a73e8;
                border-bottom: 2px solid #1a73e8;
            }
            QTabBar::tab:hover:!selected {
                background: #f1f3f4;
                border-radius: 4px;
            }
            
            /* Стиль строки поиска */
            QLineEdit {
                border: 1px solid #dfe1e5;
                border-radius: 24px;
                padding: 8px 16px;
                margin: 8px 10px;
                font-size: 14px;
                background: #ffffff;
                selection-background-color: #e8f0fe;
                min-width: 400px;
                max-width: 800px;
            }
            QLineEdit:hover {
                background: #ffffff;
                border-color: #dfe1e5;
                box-shadow: 0 1px 6px rgba(32,33,36,.28);
            }
            QLineEdit:focus {
                border-color: #4285f4;
                outline: none;
            }
            
            /* Стиль панели инструментов */
            QToolBar {
                border: none;
                background: #ffffff;
                spacing: 2px;
                padding: 4px;
            }
            
            /* Стиль кнопок */
            QToolButton {
                border: none;
                background: transparent;
                padding: 4px;
                border-radius: 20px;
                color: #5f6368;
                font-size: 16px;
                min-width: 32px;
                min-height: 32px;
            }
            QToolButton:hover {
                background: #f1f3f4;
            }
            QToolButton:pressed {
                background: #e8eaed;
            }
            QToolButton:checked {
                background: #e8f0fe;
                color: #1a73e8;
            }
            
            /* Стиль меню */
            QMenuBar {
                background: #ffffff;
                border: none;
                padding: 8px;
            }
            QMenuBar::item {
                padding: 8px 12px;
                background: transparent;
                border-radius: 4px;
                color: #5f6368;
            }
            QMenuBar::item:selected {
                background: #f1f3f4;
            }
            
            /* Стиль прогресс-бара */
            QProgressBar {
                border: none;
                background: #f1f3f4;
                height: 3px;
            }
            QProgressBar::chunk {
                background: #1a73e8;
            }
        """)

        # Создаем окно загрузок
        self.downloads_window = DownloadsWindow(self)

        # Создаем вкладки
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        # Настройка панели навигации
        navbar = QToolBar()
        navbar.setMovable(False)
        navbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                border: none;
                background: white;
                padding: 5px 10px;
            }
            QToolButton {
                border: none;
                border-radius: 4px;
                padding: 6px;
                margin: 0 2px;
            }
            QToolButton:hover {
                background: #f1f3f4;
            }
            QToolButton:pressed {
                background: #e8eaed;
            }
        """)
        self.addToolBar(navbar)

        # Кнопки навигации
        back_btn = QToolButton()
        back_btn.setText('←')
        back_btn.setFixedSize(36, 36)
        back_btn.setToolTip('Назад')
        back_btn.clicked.connect(self.back_clicked)
        navbar.addWidget(back_btn)

        forward_btn = QToolButton()
        forward_btn.setText('→')
        forward_btn.setFixedSize(36, 36)
        forward_btn.setToolTip('Вперед')
        forward_btn.clicked.connect(self.forward_clicked)
        navbar.addWidget(forward_btn)

        reload_btn = QToolButton()
        reload_btn.setText('↻')
        reload_btn.setFixedSize(36, 36)
        reload_btn.setToolTip('Обновить')
        reload_btn.clicked.connect(self.reload_clicked)
        navbar.addWidget(reload_btn)

        home_btn = QToolButton()
        home_btn.setText('⌂')
        home_btn.setFixedSize(36, 36)
        home_btn.setToolTip('Домой')
        home_btn.clicked.connect(self.navigate_home)
        navbar.addWidget(home_btn)

        # Строка поиска
        self.url_bar = QLineEdit()
        self.url_bar.setFixedHeight(36)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dfe1e5;
                border-radius: 18px;
                padding: 0 15px;
                font-size: 14px;
                background: white;
                margin: 0 10px;
            }
            QLineEdit:hover {
                background: #f1f3f4;
                border-color: #dfe1e5;
            }
            QLineEdit:focus {
                background: white;
                border-color: #4285f4;
                outline: none;
            }
        """)
        self.url_bar.setPlaceholderText('Поиск в Google или введите URL')
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Кнопки справа
        downloads_btn = QToolButton()
        downloads_btn.setText('↓')
        downloads_btn.setFixedSize(36, 36)
        downloads_btn.setToolTip('Загрузки')
        downloads_btn.clicked.connect(self.show_downloads)
        navbar.addWidget(downloads_btn)

        new_tab_btn = QToolButton()
        new_tab_btn.setText('+')
        new_tab_btn.setFixedSize(36, 36)
        new_tab_btn.setToolTip('Новая вкладка')
        new_tab_btn.clicked.connect(lambda: self.add_new_tab())
        navbar.addWidget(new_tab_btn)

        # Отключаем возможность закрытия вкладок
        self.tabs.setTabsClosable(False)

        # Создаем меню в стиле Safari
        menu = self.menuBar()
        menu.setStyleSheet("""
            QMenuBar {
                background: transparent;
                border: none;
            }
            QMenuBar::item {
                padding: 4px 10px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #e5e5e5;
                border-radius: 3px;
            }
        """)
        
        file_menu = menu.addMenu('Файл')
        
        new_tab_action = QAction('Новая вкладка', self)
        new_tab_action.setShortcut('Ctrl+T')
        new_tab_action.triggered.connect(lambda: self.add_new_tab())
        file_menu.addAction(new_tab_action)

        save_page_action = QAction('Сохранить страницу', self)
        save_page_action.setShortcut('Ctrl+S')
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)

        save_image_action = QAction('Сохранить изображение', self)
        save_image_action.triggered.connect(self.save_image)
        file_menu.addAction(save_image_action)

        # Создаем первую вкладку
        self.add_new_tab(QUrl('https://www.google.com'))

        # Настраиваем параметры загрузки
        self.download_settings()

        # Включаем возможность закрытия вкладок
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        # Обновляем стили для вкладок и кнопки закрытия
        self.setStyleSheet(self.styleSheet() + """
            QTabBar::close-button {
                color: #666666;
                margin: 2px;
                padding: 2px;
            }
            QTabBar::close-button:hover {
                background: #e8e8e8;
                border-radius: 2px;
            }
            QTabBar::close-button:pressed {
                background: #d0d0d0;
            }
            QTabBar::tab {
                padding-right: 25px;
            }
        """)

    def show_downloads(self):
        self.downloads_window.show()
        self.downloads_window.raise_()

    def download_settings(self):
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.downloadRequested.connect(self.handle_download)
            profile.setDownloadPath(downloads_path)
        except Exception as e:
            print(f"Ошибка при настройке загрузок: {str(e)}")

    def handle_download(self, download):
        try:
            default_path = os.path.join(downloads_path, download.suggestedFileName())
            path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить файл", default_path,
                "Все файлы (*.*)"
            )
            
            if path:
                download.setPath(path)
                download.accept()
                
                # Создаем виджет для отображения прогресса загрузки
                download_widget = DownloadWidget(download)
                self.downloads_window.add_download(download_widget)
                
        except Exception as e:
            print(f"Ошибка при обработке загрузки: {str(e)}")

    def show_download_complete(self, path):
        QMessageBox.information(self, "Загрузка завершена",
                              f"Файл сохранен в:\n{path}")

    def save_page(self):
        if not self.tabs.currentWidget():
            return
            
        current_url = self.tabs.currentWidget().url().toString()
        suggested_name = current_url.split('/')[-1] or 'page'
        if not suggested_name.endswith('.html'):
            suggested_name += '.html'
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить страницу",
            os.path.join(downloads_path, suggested_name),
            "HTML Files (*.html);;All Files (*.*)"
        )
        
        if path:
            self.tabs.currentWidget().page().save(path, QWebEngineDownloadItem.CompleteHtmlSaveFormat)

    def save_image(self):
        if not self.tabs.currentWidget():
            return
            
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение",
            downloads_path,
            "Images (*.png *.jpg *.jpeg);;All Files (*.*)"
        )
        
        if path:
            self.tabs.currentWidget().page().runJavaScript("""
                (function() {
                    var img = document.querySelector('img');
                    return img ? img.src : null;
                })();
            """, lambda result: self.download_image(result, path) if result else None)

    def download_image(self, url, save_path):
        if url:
            download = QWebEngineDownloadItem(QUrl(url))
            download.setPath(save_path)
            download.accept()
            download.finished.connect(lambda: self.show_download_complete(save_path))

    def back_clicked(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().back()
            
    def forward_clicked(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().forward()
            
    def reload_clicked(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().reload()

    def add_new_tab(self, qurl=QUrl('https://www.google.com')):
        try:
            browser = QWebEngineView()
            browser.setUrl(qurl)
            
            i = self.tabs.addTab(browser, 'Новая вкладка')
            self.tabs.setCurrentIndex(i)
            
            browser.urlChanged.connect(lambda qurl, browser=browser:
                self.update_urlbar(qurl, browser))
            browser.loadFinished.connect(lambda _, i=i, browser=browser:
                self.tabs.setTabText(i, browser.page().title()))
        except Exception as e:
            print(f"Ошибка при создании новой вкладки: {str(e)}")

    def close_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def navigate_home(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(QUrl('https://www.google.com'))

    def navigate_to_url(self):
        if not self.tabs.currentWidget():
            return
            
        q = QUrl(self.url_bar.text())
        if q.scheme() == '':
            q.setScheme('http')
        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser=None):
        if not browser or browser != self.tabs.currentWidget():
            return
        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def search(self):
        if not self.tabs.currentWidget():
            return
            
        search_text = self.url_bar.text()
        search_url = f'https://www.google.com/search?q={search_text}'
        self.tabs.currentWidget().setUrl(QUrl(search_url))

def main():
    try:
        if sys.platform == 'win32':
            import ctypes
            myappid = 'mycompany.mybrowser.browser.1'  # произвольный идентификатор
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
        app = QApplication(sys.argv)
        QApplication.setApplicationName('Web Browser')
        window = Browser()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        QMessageBox.critical(None, "Ошибка", f"Произошла ошибка: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
