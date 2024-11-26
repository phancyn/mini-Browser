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
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Создаем папку для загрузок, если её нет
downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads', 'WebBrowser')
if not os.path.exists(downloads_path):
    os.makedirs(downloads_path)

class DownloadWidget(QWidget):
    def __init__(self, download, parent=None):
        super().__init__(parent)
        self.download = download
        self.download_path = download.path()
        
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
        
        self.setLayout(layout)
        
        # Подключаем сигналы загрузки
        self.download.downloadProgress.connect(self.update_progress)
        self.download.finished.connect(self.download_finished)
        
        # Добавляем возможность открытия файла по двойному клику
        self.setMouseTracking(True)
        
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and os.path.exists(self.download_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.download_path))
            
    def update_progress(self, bytes_received, bytes_total):
        try:
            # Обновляем прогресс
            self.progress_bar.setMaximum(bytes_total)
            self.progress_bar.setValue(bytes_received)
            
            # Обновляем размер
            total_mb = bytes_total / (1024 * 1024)
            received_mb = bytes_received / (1024 * 1024)
            self.size_label.setText(f"{received_mb:.1f} MB / {total_mb:.1f} MB")
            
            # Вычисляем и показываем скорость
            speed = bytes_received / max(1, self.download.elapsedTime().elapsed() / 1000.0)
            speed_mb = speed / (1024 * 1024)
            self.speed_label.setText(f"{speed_mb:.1f} MB/s")
            
        except Exception as e:
            print(f"Ошибка при обновлении прогресса: {str(e)}")
            
    def download_finished(self):
        try:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.speed_label.setText("Завершено")
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
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: none;
                background: white;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background: transparent;
                border: none;
                padding: 8px 16px;
                margin: 0 2px;
                color: #666;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                color: #007AFF;
                border-bottom: 2px solid #007AFF;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                background: white;
                margin: 5px;
            }
            QToolBar {
                border: none;
                background: transparent;
                spacing: 5px;
            }
            QToolButton {
                border: none;
                background: transparent;
                padding: 5px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background: #e5e5e5;
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

        # Создаем панель навигации
        navbar = QToolBar()
        navbar.setMovable(False)
        self.addToolBar(navbar)

        # Кнопки навигации в едином стиле Safari
        back_btn = QToolButton()
        back_btn.setText('←')
        back_btn.setToolTip('Назад')
        back_btn.clicked.connect(self.back_clicked)
        navbar.addWidget(back_btn)

        forward_btn = QToolButton()
        forward_btn.setText('→')
        forward_btn.setToolTip('Вперед')
        forward_btn.clicked.connect(self.forward_clicked)
        navbar.addWidget(forward_btn)

        reload_btn = QToolButton()
        reload_btn.setText('⟳')
        reload_btn.setToolTip('Обновить')
        reload_btn.clicked.connect(self.reload_clicked)
        navbar.addWidget(reload_btn)

        # Unified Search/URL bar в стиле Safari
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText('Поиск или введите адрес')
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Кнопки справа
        share_btn = QToolButton()
        share_btn.setText('⇪')
        share_btn.setToolTip('Поделиться')
        navbar.addWidget(share_btn)

        downloads_btn = QToolButton()
        downloads_btn.setText('⬇')
        downloads_btn.setToolTip('Загрузки')
        downloads_btn.clicked.connect(self.show_downloads)
        navbar.addWidget(downloads_btn)

        tabs_btn = QToolButton()
        tabs_btn.setText('+')
        tabs_btn.setToolTip('Новая вкладка')
        tabs_btn.clicked.connect(lambda: self.add_new_tab())
        navbar.addWidget(tabs_btn)

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
        self.add_new_tab()

        # Настраиваем параметры загрузки
        self.download_settings()

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
        app = QApplication(sys.argv)
        QApplication.setApplicationName('Web Browser')
        
        # Создаем и показываем окно браузера
        window = Browser()
        window.show()
        
        # Запускаем главный цикл приложения
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        input("Нажмите Enter для выхода...")  # Добавляем паузу перед закрытием

if __name__ == '__main__':
    main()
