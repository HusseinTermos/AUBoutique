import base64
import datetime
import json
import os
import socket
import sys

import threading

from time import sleep
from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QFont, QTextCursor, QIcon, QIntValidator
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QStackedLayout, QLabel, QPushButton,
    QScrollArea, QGridLayout, QFrame, QTextEdit, QLineEdit, QFileDialog, QComboBox,
    QSpacerItem, QSizePolicy, QMessageBox, QFormLayout, QGraphicsOpacityEffect
)

from currency_data import supported_currencies, currency_symbols

url = "http://localhost:9999"

def format_price(price, currency):
    currency_symbol, is_before = currency_symbols[currency]
    if is_before: return f"{currency_symbol} {price:.2f}"
    else: return f"{price:.2f} {currency_symbol}"

MINIMUM_SIZE = (1850, 970)
NOTIFICATION_SIZE = (300, 100)
back_color = 'C4DAD2'
product_widget_color='E9EFEC'
color_ribbon='16423C'
color_buttons = '6A9C89'
hover_color = '5F8D7B'


class MainWindow(QWidget):
    """Main window containing all content"""
    def __init__(self):
        super().__init__()
        self.main_app = MainApp(self)

    def set_up_ui(self):
        """Set up inital UI for main window"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        self.setMinimumSize(*WINDOW_SIZE)

        main_layout.addWidget(self.main_app)

        self.notification_list = NotificationList(self)
        self.main_app.set_up_ui()
        self.setObjectName("main_window")
        self.setStyleSheet(
            """#main_window {background-color: #""" + back_color + """}"""
        )
                           
    def add_notification(self, title=None, body=None):
        """Add a notification to the notification list to the right"""
        self.notification_list.add_notification(title, body)
        app.processEvents()

    def new_message(self, sender):
        """Emit a signal to show a notification for new chat messages"""
        self.notification_list.emit_message_received(sender)

class MainApp(QWidget):
    """Represents main area where pages are shown"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.page_stack = QStackedLayout()

    def set_up_ui(self):
        """Setting up persistent buttons and the ribbon"""
        self.setMinimumSize(1830,950)
        outer_layout = QVBoxLayout()

        outer_layout.setContentsMargins(0, 0, 0, 0)
    
        self.setLayout(outer_layout)

        self.top_ribbon = TopRibbon()
        outer_layout.addWidget(self.top_ribbon)


    
        self.chat_button = self.create_chat_button()
        self.add_products_button = self.create_add_product_button()
        self.reposition_buttons()
        self.resizeEvent = lambda _: self.reposition_buttons()

        self.page_stack.currentChanged.connect(self.page_changed)


        outer_layout.addLayout(self.page_stack)

        # Start by taking the user to the login page
        self.redirect_to_login()

    def page_changed(self):
        """Hide ribbons and persistent buttons for certain pages"""
        if isinstance(self.page_stack.currentWidget(),  (ChatWindow,)):
            self.hide_buttons()
            self.top_ribbon.show()
        elif isinstance(self.page_stack.currentWidget(),  (LoginPage, RegisterPage)):
            self.hide_buttons()
            self.top_ribbon.hide()
        else:
            self.show_buttons()
            self.top_ribbon.show()
            self.raise_buttons([self.chat_button, self.add_products_button])

    def reposition_buttons(self):
        
        self.add_products_button.setGeometry(
            0, self.height() - 80, self.add_products_button.width(), self.add_products_button.height()
        )
        self.chat_button.setGeometry(
            self.width() - self.chat_button.width() - 10, self.height() - 80, self.chat_button.width(), self.chat_button.height()
        )
        
    def raise_buttons(self, buttons):
        """Raise buttons so they are not covered by
        other widgets
        """
        for button in buttons:
            button.raise_()

    def hide_buttons(self):
        self.add_products_button.hide()
        self.chat_button.hide()

    def show_buttons(self):
        self.add_products_button.show()
        self.chat_button.show()

    def create_chat_button(self):
        """Create UI for persistent chat button"""   
        chat_button = QPushButton("💬", self)
        chat_button.setFixedSize(75, 60)
        chat_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Default blue background */
                color: black;
                font-size: 28px;
                border-radius: 5px;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Darker blue on hover */
            }
        """)
        chat_button.setCursor(Qt.PointingHandCursor)
        chat_button.clicked.connect(self.redirect_to_chat_list)
        return chat_button
    
    def create_add_product_button(self):
        """Create UI for persistent add product button"""
        add_product_button = QPushButton("✚ Add Product", self)
        add_product_button.setFixedSize(210, 60)
        add_product_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Default blue background */   
                color: white;
                font-size: 28px;
                border-radius: 5px;
                border: none;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Darker blue on hover */
            }
        """)
        add_product_button.setCursor(Qt.PointingHandCursor)
        add_product_button.clicked.connect(main_window.main_app.redirect_to_add_product)
        return add_product_button
    
    def default_back_button_method(self):
        
        self.page_stack.removeWidget(self.page_stack.widget(self.page_stack.count() - 1))
        # Refresh chat window if user is going back to it
        if isinstance(self.page_stack.currentWidget(), ChatWindow):
            self.page_stack.currentWidget().refresh_status()
        
    """The rest of functions in this class redirect
    the user to certain pages while making sure to
    show and hide elements as appropriate"""
    def redirect_to_my_bought_products(self):
        self.parent().add_notification("Redirecting...", "Redirecting you to your bought products")
        self.top_ribbon.show()
        self.show_buttons()
        status_code, json_data = server_get_my_products(user_id)
        if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
        self.page_stack.addWidget(MyBoughtProductsPage(json_data["products"]))
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_chat_list(self):
        self.top_ribbon.show()
        self.show_buttons()
        self.page_stack.addWidget(ChatsPage())
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_search_screen(self):
        self.top_ribbon.show()
        self.show_buttons()
        self.page_stack.addWidget(SearchScreen())
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_my_products(self):
        self.parent().add_notification("Redirecting...", "Redirecting you to your products")
        self.top_ribbon.show()
        self.show_buttons()
        my_products = server_get_my_products(user_id)[1]["products"]
        self.page_stack.addWidget(MyProductsView(my_products))
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)
    
    def redirect_to_search(self):
        self.top_ribbon.show()
        self.show_buttons()
        self.page_stack.addWidget(SearchScreen())
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)
        
    def redirect_to_bought_products(self):
        self.parent().add_notification("Redirecting...", "Redirecting you to your bought products")
        self.top_ribbon.show()
        self.show_buttons()
        bought_products = server_get_bought_products(user_id)[1]["bought_products"]
        BoughtProductsPage(bought_products)
        self.page_stack.addWidget(BoughtProductsPage(bought_products))
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_add_product(self):
        self.top_ribbon.show()
        self.show_buttons()
        self.page_stack.addWidget(Add_Product_Page())
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_login(self):
        self.page_stack.addWidget(LoginPage())
        self.hide_buttons()
        self.top_ribbon.hide()
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_owner(self, owner_id, owner_name):
        if owner_id == user_id:
            self.redirect_to_my_products()
        else:
            self.parent().add_notification("Redirecting...", f"Redirecting you to {owner_name}'s products")
            status_code, _, json_data  = server_get_owner_products(owner_id)
            if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
            self.top_ribbon.show()
            self.show_buttons()
            owner_products = json_data["products"]
            is_online = json_data["is_online"]
            new_page = OwnerProductView(owner_products, owner_name, owner_id, is_online)
            self.page_stack.addWidget(new_page)
            self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_product(self, product_id):
        self.parent().add_notification("Redirecting...", "Redirecting you to the product's details")
        new_page = QWidget()
        status_code, json_data = server_get_product_info(product_id)
        if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
        self.top_ribbon.show()
        self.show_buttons()
        updated_product_data = json_data["product_data"]
        new_page = Product_Page(updated_product_data)
        self.page_stack.addWidget(new_page)
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)
    
    def redirect_to_all_products(self):
        self.parent().add_notification("Redirecting...", "Redirecting you to the homepage")
        status_code, json_data = server_get_all_products()
        if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
        all_products = json_data["products"]
        status_code, json_data = server_get_bestseller_products()
        if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
        bestseller_products = json_data["most_sold_products"]
        new_page = ProductView(all_products, bestseller_products)
        self.page_stack.addWidget(new_page)
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)
        self.top_ribbon.show()
        self.show_buttons()
                
    def redirect_to_chat(self, owner_id, owner_name):
        self.top_ribbon.show()
        self.hide_buttons()
        self.page_stack.addWidget(ChatWindow(owner_id, owner_name))
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_register(self):
        self.page_stack.addWidget(RegisterPage())
        self.top_ribbon.hide()
        self.hide_buttons()
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

    def redirect_to_search_results(self, query, min_price, max_price, sort_order):
        self.parent().add_notification("Redirecting...", "Redirecting you to the search results")
        if query is not None:
            status_code, json_data = server_search(query)
            if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
            result = json_data["results"]
        else:
            status_code, json_data = server_get_all_products()
            if status_code != 200: main_window.add_notification("Something went wrong", "Please try again")
            result = json_data["products"]

        result = [product for product in result if min_price <= product["price"] <= max_price]
        if sort_order == "Price Ascending":
            result.sort(key=lambda p: p["price"])
        elif sort_order == "Price Descending":
            result.sort(key=lambda p: p["price"], reverse=True)
        elif sort_order == "Date Added Ascending":
            result.sort(key=lambda p: datetime.datetime.strptime(p["date_time_added"], "%Y-%m-%d %H:%M:%S"))
        elif sort_order == "Date Added Descending":
            result.sort(key=lambda p: datetime.datetime.strptime(p["date_time_added"], "%Y-%m-%d %H:%M:%S"), reverse=True)
        # otherwise, server sorts by relevance
        self.page_stack.addWidget(SearchResult(result))
        self.page_stack.setCurrentIndex(self.page_stack.count() - 1)

class NotificationList(QLabel):
    """Container for notifications"""

    # Signal the is emitted when a chat message is received
    message_received = QtCore.pyqtSignal(str)
    def __init__(self, parent:QWidget):
        super().__init__(parent=parent)
        self.message_received.connect(self.add_msg_notif)
        self.notification_list = []
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        main_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setFixedSize(NOTIFICATION_SIZE[0] + 5, 0)
        self.update_position()
    
        self.hide()
    def add_msg_notif(self, sender_username):
        """Show a notification for chat messages"""
        self.add_notification("New message", f"You have a new message from {sender_username}")

    def emit_message_received(self, sender_username):
        """Emit the chat messaging signal"""
        self.message_received.emit(sender_username)
    def update_size(self):
        """Resize the widget according to the number 
        of notifications"""
        self.setFixedHeight((NOTIFICATION_SIZE[1] + 7) * len(self.notification_list))

    def add_notification(self, title=None, body=None):
        args = {"parent": self}
        if title is not None: args["title"] = title
        if body is not None: args["body"] = body
        new_notif = NotificationWidget(**args)
        self.notification_list.append(new_notif)
        self.layout().addWidget(new_notif)
        self.update_size()
        self.show()

    def remove_notification(self, notif_obj):
        try:
            self.notification_list.remove(notif_obj)
        except ValueError: pass

        self.update_size()
        if len(self.notification_list) == 0:
            self.hide()
    
    def update_position(self):
        """Calculate position based on position and deminsions of the parent"""
        window_w = self.parent().size().width()
        window_x, window_y = self.parent().pos().x(), self.parent().pos().y()
        
        notif_x = window_x + window_w - self.width() - 10
        notif_y = 115 + window_y 
        print(notif_x, notif_y, self.width(), self.height())
        self.setGeometry(notif_x, notif_y, self.width(), self.height())
        self.raise_()

class NotificationWidget(QLabel):
    """Represents a single notification"""
    # Signal to be emitted to close a notification
    close_signal = QtCore.pyqtSignal()
    def __init__(self, parent: NotificationList, title="Notification", body="You have a new notification"):        
        super().__init__()
        self.parent_notif_list = parent
        self.title = title
        self.body = body
        self.close_signal.connect(self.fade_and_close)

        # Set up GUI structure for Notification
        main_layout = QVBoxLayout()

        self.setLayout(main_layout)
        self.setFixedSize(*NOTIFICATION_SIZE)
        self.update_position()


        body_label = QLabel(f"<span style='font-size:15px; color: black;'>{body}</span>")
        body_label.setWordWrap(True)
        body_label.setFixedWidth(280)


        main_layout.addLayout(self.get_first_row())
        main_layout.addWidget(body_label, alignment=Qt.AlignLeft | Qt.AlignTop)
        self.setObjectName("NotificationWidget")
        self.setStyleSheet("""#NotificationWidget {
                           border: 1px solid black;
                           border-radius: 10px;
                           background-color: #"""+ product_widget_color + """;
                           font: Roboto;
                           }
                           """)
        
        threading.Thread(target=lambda: self.auto_close(), daemon=True).start() # Countdown before the notification closes
        
    def get_first_row(self):
        """Prepare GUI elements for title and close button"""
        layout = QHBoxLayout()

        title_label = QLabel(f"<span style='font-size:20px; color: black;'>{self.title}</span>")
        title_label.setWordWrap(True)
        title_label.setFixedWidth(260)
        layout.addWidget(title_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        close_button = QLabel(f"<span style='font-size:17px; color: black;'>✕</span>")
        close_button.setCursor(Qt.PointingHandCursor)
        close_button.mousePressEvent = lambda _: self.close_notification()
        close_button.setFixedWidth(20)
        layout.addWidget(close_button, alignment=Qt.AlignRight | Qt.AlignTop)
        return layout
    

    def auto_close(self):
        sleep(4)
        self.close_signal.emit()

    def fade_and_close(self):
        """Fade out effect for notification before it closes"""
        fade_out_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(fade_out_effect)
        
        self.fade_out_animation = QPropertyAnimation(fade_out_effect, b"opacity")
        self.fade_out_animation.setDuration(1500)
        self.fade_out_animation.setStartValue(1)
        self.fade_out_animation.setEndValue(0)
        self.fade_out_animation.finished.connect(self.close_notification)
        self.fade_out_animation.start()


    def close_notification(self):
        self.parent().remove_notification(self) # self.parent() is an instance of NotificationList
        self.hide()
        

    def update_position(self): 
        window_w = self.parent_notif_list.size().width()
        window_x, window_y = self.parent_notif_list.pos().x(), self.parent_notif_list.pos().y()
        
        notif_x = window_x + window_w - self.width() - 10
        notif_y = 38 + window_y 
        self.setGeometry(notif_x, notif_y, self.width(), self.height())

class ProductWidget(QFrame):
    """Represent the widget of a single product"""
    def __init__(self, product, is_owner_view=False):
        super().__init__()
        self.product = product
        self.is_owner_view = is_owner_view
        self.init_ui()

    def init_ui(self):
        """Set up GUI structure for Product Widget"""
        self.setCursor(Qt.PointingHandCursor)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedSize(400, 500)  
        self.setStyleSheet("""
            QFrame {
                background-color: #""" + product_widget_color + """; 
                border-radius: 10px;
            }
        """)
        product_layout = QVBoxLayout()
        product_layout.setContentsMargins(5, 5, 5, 5)

        # Container for the image
        image_container = QFrame()
        image_container.setFixedSize(350, 400)  

        image_container.setStyleSheet("""
            QFrame {
                border: no border;
                background-color: #""" + product_widget_color + """;
                border-radius: 5px;
            }
        """)

        # Product image
        pixmap = QPixmap()
        try:
            if self.product["image"]: 
                pixmap.loadFromData(base64.b64decode(self.product["image"]))
            else:
                pixmap.load("logo.jpeg")
        except Exception as e:
            print(f"Error loading image: {e}")
            pixmap.load("logo.jpeg")

        product_image = QLabel(image_container)
        if not pixmap.isNull():
            # Scale the pixmap to fit within the container
            scaled_pixmap = pixmap.scaled(
                340, 340, 
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            product_image.setPixmap(scaled_pixmap)
        else:
            product_image.setText("No Image Available")  # Fallback text for missing images
            product_image.setStyleSheet("color: #888; font-size: 14px; font-style: italic; background-color: #DCDCDC")

        product_image.setAlignment(Qt.AlignCenter)

        # Layout for the image container
        image_layout = QVBoxLayout()
        image_layout.addWidget(product_image, alignment = Qt.AlignCenter)
        image_container.setLayout(image_layout)

        product_layout.addWidget(image_container, alignment=Qt.AlignCenter)

        # Container for the details
        details_container = QFrame()
        details_container.setFixedSize(350, 120)
        details_container.setStyleSheet("""
            QFrame {
                border: no border;
                background-color: #""" + product_widget_color + """; 
                border-radius: 5px;
            }
        """)


        details_layout = QGridLayout()
        details_layout.setContentsMargins(5, 5, 5, 5)
        details_layout.setSpacing(10)

        # Product title
        product_name = QLabel(f"{self.product['name']}")
        product_name.setAlignment(Qt.AlignLeft)
        product_name.setAlignment(Qt.AlignVCenter)
        product_name.setFixedSize(340,32)
        product_name.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: black;
            background-color: #""" + product_widget_color + """;
        """)

        # Product price
        product_price = QLabel(format_price(self.product["price"], self.product["currency"]))
        product_price.setAlignment(Qt.AlignLeft)
        product_price.setAlignment(Qt.AlignVCenter)
        product_price.setFixedSize(340,32)
        product_price.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: green;
            background-color: #""" + product_widget_color + """;
        """)

        # Owner name
        if not self.is_owner_view:
            product_owner = QLabel(f"👤 {self.product.get('owner_name', "some_owner")}") # TODO: fix
            product_owner.setObjectName("owner_label")
            product_owner.setAlignment(Qt.AlignLeft)
            product_owner.setAlignment(Qt.AlignVCenter)
            product_owner.setFixedSize(250,32)
            product_owner.setCursor(Qt.PointingHandCursor)
            product_owner.setStyleSheet("""
                #owner_label {
                    font-size: 25px;
                    font-weight: bold;
                    color: #555;
                    background-color: #""" + product_widget_color + """;
                }
                #owner_label:hover {
                    text-decoration: underline;  /* Add underline on hover for indication */
                    color: black;
                }
            """)
            product_owner.mousePressEvent = lambda _: main_window.main_app.redirect_to_owner(self.product["owner_id"], self.product["owner_name"])

        # Product rating
        product_rating = QLabel(f"⭐ {self.product['avg_rating'] or 'N/A'}")
        product_rating.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        product_rating.setFixedSize(85, 32)
        product_rating.setStyleSheet("""
            font-size: 25px;
            color: #ff9800;
            background-color: #""" + product_widget_color + """;
        """)

        # Adjust column spans for layout 
        details_layout.addWidget(product_name, 0, 0, 1, 4)
        details_layout.addWidget(product_price, 1, 0, 1, 4)  
        if not self.is_owner_view:
            details_layout.addWidget(product_owner, 2, 0, 1, 3)
            details_layout.addWidget(product_rating, 2, 3, 1, 1)
        else:
            details_layout.addWidget(product_rating, 2, 0, 1, 1)

        details_container.setLayout(details_layout)
        product_layout.addWidget(details_container, alignment=Qt.AlignHCenter)

        self.setLayout(product_layout)

        self.mousePressEvent = lambda event: main_window.main_app.redirect_to_product(self.product["id"])

class ProductView(QWidget):
    """Represents the products page"""
    def __init__(self, products, bestseller_products=None, is_owner_view=False):
        super().__init__()
        self.bestseller_products = bestseller_products or []
        self.products = products
        self.is_owner_view = is_owner_view
        # self.search_screen = search_screen
        self.init_ui()

    def init_ui(self):
        # Main layout to hold everything
        layout = QVBoxLayout()

        # Container to hold the product grid
        container = QWidget()
        container.setFixedWidth(1800)
        container.setMinimumHeight(self.height())
        container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)  
        container_layout = QVBoxLayout()

        

        product_grid = self.create_product_grid()
        container_layout.addWidget(product_grid)

        container.setLayout(container_layout)
        layout.addWidget(container, alignment=Qt.AlignHCenter)


        self.setLayout(layout)



        # Add the return to top button on top of everything
        top_button = self.create_return_to_top_button()
        top_button.setParent(self)  # Make it a child of the main widget
        # top_button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Light grey with transparency
        top_button.show()
        top_button.raise_()  # Ensure it is above other widgets



        #C_container
        self.setStyleSheet("""
        QWidget {
            background-color: #""" + back_color + """;
            border-radius: 10px;
        }
        """)

    def create_product_grid(self):
        '''Set the display of the products'''
        self.scroll_area = QScrollArea()
        scroll_content = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setAlignment((Qt.AlignTop | Qt.AlignHCenter))
        grid_layout.setVerticalSpacing(20)  # Adjust the spacing value as needed

        if self.__class__ == ProductView:
            # Add the Bestsellers Title
            bestsellers_label = QLabel("Bestsellers")
            bestsellers_label.setStyleSheet("""
                font-size: 43px;
                font-weight: bold;
                color: black;
                margin-bottom: 0px;
            """)
            grid_layout.addWidget(bestsellers_label, 0, 0, 1, 4)  # Spans 4 columns
            
            # Add the Bestseller Products (Assuming exactly 4 products)
            for idx, product in enumerate(self.bestseller_products):
                grid_layout.addWidget(ProductWidget(product, self.is_owner_view), 1, idx)

        # Add the Bestsellers Title
        bestsellers_label = QLabel("All Products")
        
        bestsellers_label.setStyleSheet("""
            font-size: 40px;
            font-weight: bold;
            color: black;
            margin-bottom: 0px;
        """)
        num_cols = min(4, len(self.products))
        grid_layout.addWidget(bestsellers_label, 2, 0, 1, num_cols)  # Spans 4 columns

        for idx, product in enumerate(self.products):
            product_widget = ProductWidget(product, self.is_owner_view)
            row = (idx // num_cols) + 3
            col = idx % num_cols
            grid_layout.addWidget(product_widget, row, col)
        # if num_cols == 4:
        vertical_spacer = QSpacerItem(20, 100)
        # else:
        #     vertical_spacer = QSpacerItem(20, 200)

        grid_layout.addItem(vertical_spacer, grid_layout.rowCount(), 0, 1, num_cols)

        scroll_content.setLayout(grid_layout)
        self.scroll_area.setWidget(scroll_content)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMaximumWidth(2000)
        

        #its layout
        container_layout = QVBoxLayout()
        container_layout.addWidget(self.scroll_area)

        #adding buitton
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Push button to the right
        #button_layout.addWidget(return_to_top_button, alignment=Qt.AlignRight)

        container_layout.addLayout(button_layout)




        
        container_widget = QWidget()
        container_widget.setLayout(container_layout)

        return container_widget


    def back_button_method(self):
        print("Back button clicked!")
    


    def create_return_to_top_button(self):
        return returnToTop("↑ Top", self.scroll_area)

class returnToTop(QPushButton):
    '''Go back to the top of the page'''
    def __init__(self, text, scroll_area, parent=None):
        super().__init__(text, parent=parent)
        self.scroll_area = scroll_area

        self.setCursor(Qt.PointingHandCursor)

        self.setFixedSize(100, 50)
        self.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Green background */
                color: white;
                font-size: 25px;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+"""; /* Darker green on hover */
            }
        """)
        self.clicked.connect(self.scroll_to_top)
        
        self.setGeometry(
            WINDOW_SIZE[0] // 2 - 75, WINDOW_SIZE[1] - 300, self.width(), self.height()
        )
        print(WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] - 140, self.width(), self.height())
        self.raise_()


    def scroll_to_top(self):
        animation = QPropertyAnimation(self.scroll_area.verticalScrollBar(), b"value")
        animation.setDuration(500)  # Duration in milliseconds
        animation.setStartValue(self.scroll_area.verticalScrollBar().value())
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        self.animation = animation

class OwnerProductView(ProductView):
    '''Set the look of the product with seller's name'''
    def __init__(self, products, owner_name, owner_id, is_online):
        self.owner_id = owner_id
        self.owner_name = owner_name
        self.is_online = is_online
        super().__init__(products, is_owner_view=True)

    def init_ui(self):
        #main layout
        layout = QVBoxLayout()

        #container for widegts
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        '''
        #add top ribbon
        top_ribbon_layout = self.create_top_ribbon()
        layout.addWidget(top_ribbon_layout)'''

        #ribbon add
        ribbon = self.create_owner_ribbon()
        container_layout.addWidget(ribbon, alignment=Qt.AlignTop)

        #add product grid
        product_grid = self.create_product_grid()
        container_layout.addWidget(product_grid)  


        container.setLayout(container_layout)
        layout.addWidget(container, alignment= Qt.AlignHCenter)


        # Set the main layout
        self.setLayout(layout)


        self.setStyleSheet("""
        QWidget {
            background-color: #"""+back_color+""";
            border: none;
        }
        """)

        #screen_geometry = QApplication.desktop().screenGeometry()
        #self.setFixedSize(screen_geometry.width(), screen_geometry.height())
        #self.setFixedWidth(1800)
        self.setMinimumSize(1800,950)

    def create_owner_ribbon(self):
        ribbon = QWidget()
        ribbon_layout = QHBoxLayout()

        owner_label = QLabel(f"👤 {self.owner_name}")
        owner_label.setStyleSheet("""
            font-size: 40px;
            font-family: 'Arial', sans-serif;
            font-weight: bold;
            color: white;
        """)

        chat_button = QPushButton("💬")
        chat_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Light blue background */
                color: white;
                font-size: 35px;
                border-radius: 10px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Slightly darker blue on hover */
            }
        """)
        chat_button.clicked.connect(lambda: main_window.main_app.redirect_to_chat(self.owner_id, self.owner_name))


        ribbon_layout.addWidget(owner_label)
        ribbon_layout.addStretch()
        ribbon_layout.addWidget(chat_button)

        ribbon.setStyleSheet("""
            background-color: #"""+color_ribbon+""";
            padding: 10px;
            color: white;
        """)
        ribbon.setFixedSize(1800, 80)
        ribbon.setLayout(ribbon_layout)
        return ribbon

class MyProductsView(ProductView):
    '''User viewing his products'''
    def __init__(self, products):
        super().__init__(products, is_owner_view=True)

    def init_ui(self):
        #main layout
        layout = QVBoxLayout()

        #container for widegts
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        #ribbon add
        ribbon = self.create_my_products_ribbon()
        container_layout.addWidget(ribbon, alignment=Qt.AlignTop)

        #add product grid
        product_grid = self.create_product_grid()
        container_layout.addWidget(product_grid)  


        container.setLayout(container_layout)
        layout.addWidget(container, alignment=Qt.AlignHCenter)


        # Set the main layout
        self.setLayout(layout)
    
        self.setStyleSheet("""
        QWidget {
            background-color: #"""+back_color+""";
            border: none;
        }
        """)

        #screen_geometry = QApplication.desktop().screenGeometry()
        #self.setFixedSize(screen_geometry.width(), screen_geometry.height())
        self.setMinimumSize(1800,950) #M idk what does this change

    def create_my_products_ribbon(self):
        ribbon = QWidget()
        ribbon_layout = QHBoxLayout()

        # spacer_left = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # ribbon_layout.addSpacerItem(spacer_left)

        # Add "My Products" label
        my_products_label = QLabel("🏠 My Products")
        my_products_label.setAlignment(Qt.AlignVCenter)  # Align text in the middle vertically and horizontally
        my_products_label.setStyleSheet("""
            font-size: 40px;
            font-family: 'Arial', sans-serif;
            font-weight: bold;
            color: white;
        """)

        # Add this section after the user_name_button
        sold_products_button = QPushButton("Sold Products", self)
        sold_products_button.setFixedSize(200, 50)
        sold_products_button.setCursor(Qt.PointingHandCursor)
        sold_products_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Light blue background */
                color: white;
                font-size: 25px;
                border-radius: 5px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Slightly darker blue on hover */
            }
        """)
        sold_products_button.clicked.connect(main_window.main_app.redirect_to_my_bought_products)

        ribbon_layout.addWidget(my_products_label)
        ribbon_layout.addStretch()  # Pushes content to the left
        ribbon_layout.addWidget(sold_products_button, alignment=Qt.AlignLeft)

        ribbon.setStyleSheet("""
            background-color: #"""+color_ribbon+""";
            padding: 10px;
        """)
        ribbon.setFixedSize(1800, 90)
        ribbon.setLayout(ribbon_layout)
        return ribbon

class SearchScreen(QWidget):
    '''Set the look of the search screen'''
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()


        # Add the central search area
        central_area = self.create_central_area()
        main_layout.addWidget(central_area, alignment=Qt.AlignHCenter | Qt.AlignTop)


        # Apply styles
        self.setStyleSheet("""
        QWidget {
            background-color: #"""+product_widget_color+""";
        }
        QLineEdit, QComboBox {
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 5px;
        }
        QPushButton {
            background-color: #"""+color_buttons+""";  /* Green */
            color: white;
            border-radius: 5px;
            padding: 10px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #"""+hover_color+""";  /* Darker green */
        }
        QLabel {
            font-size: 30px;
        }
        """)
        self.setLayout(main_layout)
        self.setMinimumSize(1800, 1000)

    def create_central_area(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(30)


        # Main Header
        main_header = QLabel("AUBoutique Search Engine")
        main_header.setStyleSheet("""
            font-size: 40px;
            font-weight: bold;
            color: black;
            margin-bottom: 20px;
        """)
        main_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(main_header)

        '''search box'''
        search_bar_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search term...")
        self.search_input.setFixedWidth(500)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #"""+back_color+""";
                font-size: 20px;
                color: black;
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        search_bar_layout.addWidget(self.search_input)

        layout.addLayout(search_bar_layout)

        # Filters Section Header
        '''Filters box to filter the search options'''
        filters_header = QLabel("Filters")
        filters_header.setStyleSheet("""
            font-size: 35px;
            font-weight: bold;
            color: black;
            margin-bottom: 10px;
        """)
        filters_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(filters_header)

        # Filters Section
        filters_widget = QWidget()
        filters_widget.setFixedSize(600,200)
        filters_layout = QVBoxLayout()
        filters_layout.setSpacing(15)
        filters_layout.setContentsMargins(50, 20, 50, 20)

        # Min Price
        min_price_layout = QHBoxLayout()
        min_price_label = QLabel("Min Price:")
        min_price_label.setFixedWidth(170)
        min_price_label.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #333;
        """)
        self.min_price_input = QLineEdit()
        self.min_price_input.setPlaceholderText("0")
        self.min_price_input.setFixedWidth(150)
        self.min_price_input.setStyleSheet("""
            QLineEdit {
                background-color: #"""+back_color+""";
                color: black;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        min_price_layout.addWidget(min_price_label)
        min_price_layout.addWidget(self.min_price_input)
        filters_layout.addLayout(min_price_layout)

        # Add a line break for better visuals
        filters_layout.addSpacing(10)

        # Max Price
        max_price_layout = QHBoxLayout()
        max_price_label = QLabel("Max Price:")
        max_price_label.setFixedWidth(170)
        max_price_label.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #333;
        """)
        self.max_price_input = QLineEdit()
        self.max_price_input.setPlaceholderText("100000000")
        self.max_price_input.setFixedWidth(150)
        self.max_price_input.setStyleSheet("""
            QLineEdit {
                background-color: #"""+back_color+""";
                color: black;
                font-size: 16px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        max_price_layout.addWidget(max_price_label)
        max_price_layout.addWidget(self.max_price_input)
        filters_layout.addLayout(max_price_layout)

        filters_widget.setLayout(filters_layout)
        filters_widget.setStyleSheet("background-color: #F9F9F9; border-radius: 10px; padding: 20px;")

        # Sorting Section
        sorting_widget = QWidget()
        sorting_widget.setFixedSize(600,100)
        sorting_layout = QHBoxLayout()
        sorting_layout.setContentsMargins(50, 20, 50, 20)

        sort_label = QLabel("   Sort By:")
        sort_label.setFixedSize(170,50)
        sort_label.setStyleSheet("""
            font-size: 25px;
            font-weight: bold;
            color: #333;
            padding: 0px
        """)
        self.sorting_dropdown = QComboBox()
        self.sorting_dropdown.addItems(["Relevance Ascending", "Price Ascending", "Price Descending", "Date Added Ascending", "Date Added Descending"])
        self.sorting_dropdown.setFixedWidth(250)
        self.sorting_dropdown.setStyleSheet("""
            QComboBox {
                background-color: #"""+color_buttons+""";
                font-size: 16px;
                color: white;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #"""+hover_color+""";
                selection-background-color: #"""+hover_color+""";
                selection-color: white;
            }
        """)
        sorting_layout.addWidget(sort_label,alignment=Qt.AlignHCenter)
        sorting_layout.addWidget(self.sorting_dropdown)

        sorting_widget.setLayout(sorting_layout)
        sorting_widget.setStyleSheet("background-color: #F9F9F9; border-radius: 10px; padding: 20px;")

        # Search Button
        search_button = QPushButton("🔍 Search")
        search_button.setFixedSize(200, 50)
        search_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Green */
                font-size: 20px;
                font-weight: bold;
                color: white;
                border-radius: 10px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Darker green */
            }
        """)
        search_button.clicked.connect(self.execute_search)

        # Add Widgets to Layout
        '''Design and spacing'''
        layout.addWidget(filters_widget, alignment=Qt.AlignCenter)
        layout.addSpacing(10)  # Spacing between sections
        layout.addWidget(sorting_widget, alignment=Qt.AlignCenter)
        layout.addSpacing(20)  # Spacing before the button
        layout.addWidget(search_button, alignment=Qt.AlignCenter)
        central_widget.setFixedSize(800,800)

        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        central_widget.setLayout(layout)
        return central_widget



    def execute_search(self):
        query = self.search_input.text().strip() or None
        min_price = self.min_price_input.text()
        max_price = self.max_price_input.text()
        sort_order = self.sorting_dropdown.currentText()

        if min_price == '': min_price = float('-inf')
        else: min_price = int(min_price)
        if max_price == '': max_price = float('inf')
        else: max_price = int(max_price)
        # server_search(query)
        # print(f"Executing search: Min Price={min_price}, Max Price={max_price}, Sort={sort_order}")
        main_window.main_app.redirect_to_search_results(query, min_price, max_price, sort_order)
    #H must add server_search

    def go_back(self):
        print("Navigate back to previous screen")

class SearchResult(ProductView):
    def __init__(self, products):
        super().__init__(products)

class TopRibbon(QLabel):
    '''Top ribbon display including the logo, name, and other details'''
    def __init__(self, parent=None):
        super().__init__(parent)
        # Ribbon layouts
        top_ribbon_layout = QHBoxLayout()

        #C_ribbon
        self.setStyleSheet("""
            background-color: #"""+color_ribbon+""";  /* Dark grey background for the entire ribbon */
            border-radius: 10px;
            padding: 5px;
        """)

        top_ribbon_layout.setContentsMargins(10, 10, 10, 10)
        top_ribbon_layout.setSpacing(20)

        # Back button with Unicode arrow
        back_button = QPushButton("↩", self)
        back_button.setFixedSize(50, 50)
        back_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Dark grey */
                color: white;
                font-size: 50px;
                border: none;
                border-radius: 5px;
                font-weight: 900;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Slightly lighter grey on hover */
            }
        """)
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.clicked.connect(main_window.main_app.default_back_button_method)
        top_ribbon_layout.addWidget(back_button, alignment=Qt.AlignLeft)


        # Logo with a border to make it more visible
        logo_pixmap = QPixmap("logo.jpeg")
        if logo_pixmap.isNull():
            print("Error: logo failed to load!!!")
        else:
            logo_pixmap = logo_pixmap.scaled(300, 75, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_button = QPushButton(self)
            logo_button.setIcon(QIcon(logo_pixmap))
            logo_button.setIconSize(logo_pixmap.size())
            logo_button.setFixedSize(logo_pixmap.width(), logo_pixmap.height())

            # Remove the button's default border and background
            logo_button.setStyleSheet("""
                QPushButton {
                    border: none;  /* Remove border */
                    background-color: transparent;  /* Transparent background */
                }
            """)

            # Connect the button to a function
            logo_button.clicked.connect(main_window.main_app.redirect_to_all_products)

            top_ribbon_layout.addWidget(logo_button)

        # Username label with improved styling (lighter color for contrast)
        print("username:", username)
        user_name_button = QPushButton(username)
        self.user_name_button = user_name_button
        user_name_button.setMinimumWidth(120)
        user_name_button.setFixedHeight(50)
        #user_name_button.setAlignment(Qt.AlignCenter)
        user_name_button.setStyleSheet("""
            QPushButton {
                font-size: 30px;
                font-weight: bold;
                color: #f5f5f5;  /* Lighter text for better contrast */
                background-color: transparent;  /* Make the button background transparent */
                border: none;  /* Remove border for label-like appearance */
                padding: 0 10px;
            }
            QPushButton:hover {
                text-decoration: underline;  /* Add underline on hover for indication */
            }
        """)
        user_name_button.clicked.connect(lambda : main_window.main_app.redirect_to_my_products())
        top_ribbon_layout.addWidget(user_name_button)

        top_ribbon_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))


        # Add this section after the user_name_button
        bought_products_button = QPushButton("Bought Products", self)
        bought_products_button.setFixedSize(200, 50)
        bought_products_button.setCursor(Qt.PointingHandCursor)
        bought_products_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Light blue background */
                color: white;
                font-size: 25px;
                border-radius: 5px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Slightly darker blue on hover */
            }
        """)
        bought_products_button.clicked.connect(main_window.main_app.redirect_to_bought_products)

        # Add the button to the layout
        top_ribbon_layout.addWidget(bought_products_button)




        #search button
        go_button = QPushButton("Search 🔎", self)
        go_button.setFixedSize(150, 50)
        go_button.setCursor(Qt.PointingHandCursor)
        go_button.setStyleSheet("""
            QPushButton {
            background-color: #"""+color_buttons+""" ;  /* Green background */
            color: white;
            font-size: 25px;
            border-radius: 5px;
            border: none;
            padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+"""; /* Darker green on hover */
            }
        """)
        go_button.clicked.connect(main_window.main_app.redirect_to_search_screen)

        '''top_ribbon_layout.addWidget(search_box)'''
        top_ribbon_layout.addWidget(go_button)


        '''# Currency dropdown with nice spacing and styling
        currency_label = QLabel("Currency:")
        currency_label.setFixedHeight(50)
        currency_label.setStyleSheet("""
            background-color: #4CAF50
            font-size: 30px;
            color: #f5f5f5;  /* Light text color */
        """)'''

        self.currency_combo = QComboBox(self)
        self.currency_combo.setCursor(Qt.PointingHandCursor)

        for code, name in supported_currencies.items():
            self.currency_combo.addItem(name, code)
        self.currency_combo.currentIndexChanged.connect(self.currency_changed)
        self.currency_combo.setFixedWidth(450)
        self.currency_combo.setFixedHeight(50)
        self.currency_combo.setStyleSheet("""
            background-color: #"""+color_buttons+""";  /* Darker background for combo box */
            color: white;  /* White text */
            font-size: 25px;
            border-radius: 5px;
            padding: 5px;
        """)
        self.currency_combo.setCurrentIndex(list(supported_currencies.keys()).index("USD"))

        #top_ribbon_layout.addWidget(currency_label)
        top_ribbon_layout.addWidget(self.currency_combo)

        # Set the layout to the ribbon widget
        self.setLayout(top_ribbon_layout)
        self.setFixedHeight(100)

    def set_username(self, username):
        self.user_name_button.setText(username)
    
    def currency_changed(self):
        global chosen_currency
        chosen_currency = self.currency_combo.currentData()
        page_stack = main_window.main_app.page_stack
        cur_page = page_stack.currentWidget()
        if isinstance(cur_page, ProductView):
            main_window.main_app.redirect_to_all_products()
            page_stack.removeWidget(cur_page)
        elif isinstance(cur_page, Product_Page):
            main_window.main_app.redirect_to_product(cur_page.product_data["id"])
            page_stack.removeWidget(cur_page)
        elif isinstance(cur_page, BoughtProductsPage):
            main_window.main_app.redirect_to_bought_products()
            page_stack.removeWidget(cur_page)
        elif isinstance(cur_page, MyBoughtProductsPage):
            main_window.main_app.redirect_to_my_bought_products()
            page_stack.removeWidget(cur_page)

class Add_Product_Page(QWidget):
    '''Display how products are added'''
    def __init__(self):
        super().__init__()
        self.image_path = ''
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Container setup
        container = QLabel()
        container.setFixedSize(1000, 700)  # Increased size
        container.setStyleSheet(f"background-color: #{product_widget_color}; border-radius: 10px; padding: 20px; color:black; font-size: 35px;")
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)

        main_layout.addWidget(container, alignment=Qt.AlignCenter)

        # Product Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Product Name:")
        name_label.setFont(QFont("Arial", 35))
        self.name_text_box = QLineEdit()
        self.name_text_box.setFixedSize(350, 50)
        self.name_text_box.setStyleSheet(f"background-color: #{back_color}; border-radius: 5px; padding: 5px; color:black; font-size: 20px;")
        self.name_text_box.setPlaceholderText("Enter product name...")


        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_text_box)
        name_layout.addStretch()
        container_layout.addLayout(name_layout)

        # Price and Quantity
        price_quantity_layout = QHBoxLayout()

        # Price
        price_label = QLabel("Price:")
        price_label.setFont(QFont("Arial", 35))
        self.price_text_box = QLineEdit()
        self.price_text_box.setValidator(QIntValidator())
        self.price_text_box.setFixedSize(200, 50)
        self.price_text_box.setStyleSheet(f"background-color: #{back_color}; margin-left: 15px; border-radius: 5px; padding: 5px; color:black; font-size: 20px;")
        self.price_text_box.setPlaceholderText("Enter price...")


        # Quantity
        quantity_label = QLabel("Quantity:")
        quantity_label.setFont(QFont("Arial", 35))
        self.quantity_text_box = QLineEdit()
        self.quantity_text_box.setValidator(QIntValidator())
        self.quantity_text_box.setFixedSize(200, 50)
        self.quantity_text_box.setStyleSheet(f"color:black; background-color: #{back_color}; border-radius: 5px; padding: 5px;  font-size: 20px;")
        self.quantity_text_box.setPlaceholderText("Enter quantity...")


        price_quantity_layout.addWidget(price_label)
        price_quantity_layout.addWidget(self.price_text_box)
        price_quantity_layout.addStretch()  # Space between price and quantity
        price_quantity_layout.addWidget(quantity_label)
        price_quantity_layout.addWidget(self.quantity_text_box)
        price_quantity_layout.addStretch()  # Space between price and quantity
        
        container_layout.addLayout(price_quantity_layout)

        # Image Selection
        image_layout = QHBoxLayout()
        image_label = QLabel("Image:")
        image_label.setFont(QFont("Arial", 35))
        self.choose_image_button = QPushButton("Choose Image")
        self.choose_image_button.setCursor(Qt.PointingHandCursor)
        self.choose_image_button.setFixedSize(200, 50)
        self.choose_image_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #{color_buttons};
                color: white;
                border-radius: 5px;
                padding: 5px;
                font-size: 25px;
                text-align: center; 
            }}
            QPushButton:hover {{
                background-color: #{hover_color};
            }}
        """)
        self.choose_image_button.clicked.connect(self.get_image_path)

        image_layout.addWidget(image_label)
        image_layout.addWidget(self.choose_image_button)
        image_layout.addStretch()
        container_layout.addLayout(image_layout)

        # Description
        description_layout = QVBoxLayout()
        desc_label = QLabel("Description:")
        desc_label.setFont(QFont("Arial", 35))
        self.desc_text_box = QLineEdit()
        self.desc_text_box.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self.desc_text_box.setFixedSize(800, 100)  # Larger height
        self.desc_text_box.setStyleSheet(f"""background-color: #{back_color}; border-radius: 5px; padding: 5px; color:black; font-size: 20px;""")
        self.desc_text_box.setPlaceholderText("Enter product description...")


        description_layout.addWidget(desc_label)
        description_layout.addWidget(self.desc_text_box, alignment=Qt.AlignCenter)
        container_layout.addLayout(description_layout)

        # Add Product Button
        add_product_button = QPushButton("Add Product")
        add_product_button.setFixedSize(170, 60)
        add_product_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #{color_buttons};
                color: white;
                font-size: 25px;
                border-radius: 5px;
                padding: 5px;
                text-align: center; 
            }}
            QPushButton:hover {{
                background-color: #{hover_color};
            }}
        """)
        add_product_button.clicked.connect(self.add_product)
        add_product_button.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(add_product_button, alignment=Qt.AlignCenter)

  
    def get_image_path(self):
        self.image_path, _ = QFileDialog.getOpenFileName(self)
        if self.image_path != '':
            file_name = os.path.split(self.image_path)[-1]
            self.choose_image_button.setText(file_name)


    def add_product(self):
        # self.clear_errors()

        name = self.name_text_box.text()
        image_path = self.image_path
        price = self.price_text_box.text()
        currency = chosen_currency 
        desc = self.desc_text_box.text()
        quantity = self.quantity_text_box.text()

        missing_fields = []
        if name == '':
            missing_fields.append("Name")
        if image_path == '':
            missing_fields.append("Image")
        if price == '':
            missing_fields.append("Price")
        if desc == '':
            missing_fields.append("Description")
        if quantity == '':
            missing_fields.append("Quantity")
        print(currency)
        if missing_fields == []:
            status_code, _, _ = server_add_product(name, image_path, price, currency, desc, quantity)
            if status_code == 200:
                self.successfully_added()
            else:
                self.couldnt_add()
        else:
            main_window.add_notification("Missing Field(s)", "Please fill out the following fields: " + ", ".join(missing_fields))
        
    def successfully_added(self):
        '''Successful addition of product'''
        # self.response_label.setText("Succesfully added!")
        # self.response_label.setStyleSheet("font-size: 30px; color: green; font-weight: bold;")
        self.parent().parent().add_notification("Successfully added!", "Your product was added successfully!")
        self.name_text_box.setText('')
        self.price_text_box.setText('')
        self.quantity_text_box.setText('')
        self.image_path = ''
        self.choose_image_button.setText("Choose Image")
        self.desc_text_box.setText('')

    def couldnt_add(self):
        '''Unsuccessful addition with notification message'''
        main_window.add_notification("Something went wrong", "Couldn't add your product")

class Product_Page(QWidget):
    def __init__(self, product_data):
        super().__init__()
        self.product_data = product_data
        self.create_product_page()

    def create_product_page(self):
        outer_layout = QHBoxLayout()
        self.setLayout(outer_layout)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        wrapper_widget = QWidget()
        main_layout = QVBoxLayout()
        name_label = self.get_name_label(self.product_data["name"], self.product_data["quantity"])
        image_layout = self.get_image_layout()
        owner_and_price_layout = self.get_owner_and_price_layout()
        description_widget = self.get_description_widget(self.product_data["description"])

        outer_layout.addWidget(scroll_area)
        scroll_area.setWidget(wrapper_widget)
        wrapper_widget.setLayout(main_layout)

        main_layout.addWidget(name_label)
        main_layout.addLayout(image_layout)
        main_layout.addLayout(owner_and_price_layout)
        main_layout.addWidget(description_widget)
        main_layout.addWidget(self.get_rating_widget())
        if self.product_data["quantity"] > 0 and self.product_data["owner_id"] != user_id:
            main_layout.addWidget(self.get_buy_widget())

        outer_layout.setAlignment(Qt.AlignCenter)

        wrapper_widget.setObjectName("outer_label")
        wrapper_widget.setStyleSheet("#outer_label {border: none; border-radius:15px; background-color: #"+ product_widget_color + "}")
        # wrapper_label.setStyleSheet("border: 2px solid black")
        wrapper_widget.setFixedSize(850, 1000)
        scroll_area.setFixedSize(880, 860)
        scroll_area.setObjectName("prdct_scroll")
        scroll_area.setStyleSheet("#prdct_scroll {background-color: #" + product_widget_color + ";" + 
                                  "border: none; border-radius:15px; padding-bottom: 5px;}")
        
        main_layout.setAlignment(QtCore.Qt.AlignHCenter)        
          
    def get_rating_widget(self):
        wrapper_widget = QWidget()
        main_layout = QHBoxLayout()

        wrapper_widget.setLayout(main_layout)
        wrapper_widget.setFixedSize(710, 100)
        rating_label = QLabel(f"<span style='color: #efbf04; font-size: 50px;'>★</span>" +
               f"<span style='color: black; font-size: 50px;'>" +
               f"{self.product_data["avg_rating"] or "N/A"}</span>" +
               f"<span style='color: black; font-size: 20px;'>({self.product_data["rating_count"]})</span>")
        rating_label.setStyleSheet("color: #efbf04; font-size: 50px;")
        main_layout.addWidget(rating_label)
        main_layout.setAlignment(Qt.AlignCenter)
        return wrapper_widget
    
    def get_buy_widget(self):
        wrapper_widget = QWidget()
        main_layout = QHBoxLayout()

        wrapper_widget.setLayout(main_layout)

        wrapper_widget.setFixedSize(710, 100)

        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.get_buy_quantity())
        main_layout.addWidget(self.get_buy_button())

        return wrapper_widget

    def get_buy_quantity(self):
        self.quantity_selector = QComboBox()
        self.quantity_selector.setStyleSheet("""
            background-color: #"""+color_buttons+""";  /* Darker background for combo box */
            color: white;  /* White text */
            font-size: 15px;
            border-radius: 5px;
            padding: 5px;
        """)
        self.quantity_selector.addItems(map(str, range(1, self.product_data["quantity"]+1)))
        self.quantity_selector.setFixedSize(100, 40)
        return self.quantity_selector
    
    def get_buy_button(self):
        buy_button = QPushButton("Buy")
        buy_button.setStyleSheet("""
            QPushButton {
            background-color: #"""+color_buttons+""" ;  /* Green background */
            color: white;
            font-size: 25px;
            border-radius: 5px;
            border: none;
            padding: 2px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+"""; /* Darker green on hover */
            }
        """)
        buy_button.setFixedSize(100, 40)
        buy_button.clicked.connect(self.buy_product)
        return buy_button

    def buy_product(self):
        '''Product purchase with messages showing success or failure of the purchase'''
        quantity = int(self.quantity_selector.currentText())
        print(self.product_data.keys())
        product_id = self.product_data["id"]
        status_code, json_data = server_buy_product(product_id, quantity)
        if status_code != 200:
            main_window.add_notification("Couldn't process purchase", "Something went wrong...")
        else:
            main_window.add_notification("Purchase Successful", f"Please pick up your item(s) on {json_data["pickup_time"]} from the AUB post office")

    def get_image_layout(self):
        outer_layout = QHBoxLayout()
        image_label = QLabel()
        image_pixmap = QPixmap()

        outer_layout.addWidget(image_label)
        # outer_layout.setAlignment(Qt.AlignCenter)

        # image_label.setFrameStyle(QFrame.Box | QFrame.Plain)

        image_raw_file = base64.b64decode(self.product_data["image"])
        image_pixmap.loadFromData(image_raw_file)
        image_pixmap = image_pixmap.scaled(600, 400, QtCore.Qt.KeepAspectRatio, Qt.SmoothTransformation)
        

        image_label.setPixmap(image_pixmap)
        
        image_label.setFixedSize(image_pixmap.size())
        image_label.setStyleSheet("border: no border;")
        image_label.setAlignment(Qt.AlignCenter)
        return outer_layout
    
    def get_owner_and_price_layout(self):
        name_and_price_layout = QHBoxLayout()
        name_and_price_layout.addWidget(self.get_owner_label(self.product_data["owner_name"]))
        name_and_price_layout.addWidget(self.get_price_label())
        return name_and_price_layout

    def get_name_label(self, product_name, product_quantity):
        l = QLabel(f"{product_name} | {product_quantity} Pcs")
        l.setFont(QFont("Arial", 30, weight=QFont.Bold))
        l.setStyleSheet("color : #555;")
        l.setFixedSize(700, 100)
        return l

    def get_owner_label(self, owner_name):
        l = QLabel("👤 " + owner_name)
        l.setCursor(Qt.PointingHandCursor)
        l.setObjectName("owner_label2")
        l.setStyleSheet("""
            #owner_label2 {
                font-size: 35px;
                font-weight: bold;
                color: #555;
            }
            #owner_label2:hover {
                text-decoration: underline;  /* Add underline on hover for indication */
                color: black;
            }
        """)
        l.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        l.adjustSize()
        text_height, text_width = l.size().height, l.size().width
        # print(l.size())
        l.setFixedSize(l.sizeHint())
        # print(l.size())
        l.mousePressEvent = lambda x: main_window.main_app.redirect_to_owner(self.product_data["owner_id"], self.product["owner_name"])
        return l
    
    def get_price_label(self):
        price = self.product_data["price"]
        currency = self.product_data["currency"]
        l = QLabel(format_price(price, currency))
        l.setFont(QFont("Arial", 20))
        l.setStyleSheet("color: #555")
        l.setFixedSize(300, 100)
        l.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        return l

    def get_description_widget(self, description):
        description_widget = QLabel()
        main_layout = QVBoxLayout()
        title = QLabel("Description:")
        body = QLabel(description)

        description_widget.setLayout(main_layout)

        title.setFont(QFont("Arial", 17, weight=QFont.Medium))
        title.setStyleSheet("padding: 0px 0px 0px 5px; color:#555")

        body.setFont(QFont("Arial", 12))
        body.setStyleSheet("padding: 0px 0px 0px 9px; color:#555")
        body.setAlignment(Qt.AlignTop)
        body.setWordWrap(True)

        main_layout.addWidget(title)
        main_layout.addWidget(body)
        
        description_widget.setObjectName("desc")
        description_widget.setStyleSheet("""#desc {border: none; border-radius:15px; background-color:#"""+back_color+""";}""")
        description_widget.setFixedSize(700, 150)

        return description_widget

class ChatsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Main Layout for the page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title for the page
        title = QLabel("Chats 💬")
        title.setStyleSheet("""
            font-size: 55px;
            font-weight: bold;
            color: #2C2F38;
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Scroll Area for the product list
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(f"""
            background-color: #"""+back_color+""";
            border: no border;
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(1500)
        scroll_area.setAlignment(Qt.AlignTop)

        # Container widget for the products
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(20)  # Space between products

        # Add products to the layout
        # chat_data_fake = {1: {"username": "hat31"}, 2: {"username": "hat32"}, 3: {"username": "hat33"}}
        for user_id in chat_data:
            username = chat_data[user_id]["username"]
            contact_widget = self.create_contact_widget(username, user_id)
            container_layout.addWidget(contact_widget)
            # contact_widget.setFixedWidth(1400)  # Make each product widget fill the container width


        # Center the product grid horizontally
        container_layout.setAlignment(Qt.AlignCenter)

        container.setFixedWidth(1500)  # Ensure the container fills the scroll area width

        # Set container layout
        container.setLayout(container_layout)
        scroll_area.setWidget(container)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area, alignment=Qt.AlignHCenter)

        # Set main layout to the page
        self.setLayout(main_layout)

    def create_contact_widget(self, username, user_id):
        # Main widget for a single product
        product_widget = QLabel(username)
        # product_widget.setFrameShape(QFrame.StyledPanel)
        product_widget.setStyleSheet("""
                background-color: #"""+product_widget_color+""";
                border: no border;
                border-radius: 10px;
                color: black;
                font-size: 40px;
        """)
        product_widget.setFixedWidth(700)
        product_widget.setFixedHeight(100)  # Increased height for better spacing
        product_widget.setAlignment(Qt.AlignCenter)

        product_widget.mousePressEvent = lambda _: main_window.main_app.redirect_to_chat(user_id, username)
        
        return product_widget
    
class ChatWindow(QWidget):
    '''Display of the chat'''
    new_message = QtCore.pyqtSignal()
    change_status = QtCore.pyqtSignal(bool)
    def __init__(self, other_user_id, other_user_name):
        super().__init__()
        self.other_user_id = other_user_id
        self.other_user_name = other_user_name
        self.new_message.connect(self.display_new_messages)
        self.change_status.connect(self.change_status_handler)
        self.is_online = True
        self.first_undisplayed_message = 0
        self.init_ui()
        self.refresh_status()

    def emit_new_message_signal(self):
        self.new_message.emit()
    def emit_change_status(self, new_status):
        self.change_status.emit(new_status)
    def init_ui(self):
        main_window.setMinimumSize(400, 400)
        self.setWindowTitle("Chat")
        # self.setGeometry(500, 300, 400, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Ribbon (header) with seller's username, online status, and date
        self.header_ribbon = self.create_chat_ribbon()
        
        main_layout.addWidget(self.header_ribbon, alignment=Qt.AlignHCenter)

        
        # self.chat_area = QTextEdit(self)
        # self.chat_area.setReadOnly(True)

        # main_layout.addWidget(self.chat_area)

        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setStyleSheet(f"background-color: #{product_widget_color}; color: black; font-size: 30px;")
        self.chat_area.setReadOnly(True)
        # self.chat_area.setStyleSheet("padding: 100px; background-color: white;")d)
        main_layout.addWidget(self.chat_area)

        # Message input and send button layout
        bottom_layout = QHBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setFixedSize(1300, 100)
        self.message_input.setWordWrapMode(True)

        self.message_input.setStyleSheet(f"background-color: #{product_widget_color}; color: black; font-size: 25px;")
        self.message_input.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        bottom_layout.addWidget(self.message_input)


        self.send_button = QPushButton("Send", self)
        self.send_button.setFixedSize(200, 100)
        self.send_button.setCursor(Qt.PointingHandCursor)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #"""+color_buttons+""";  /* Light blue background */
                color: white;
                font-size: 30px;
                border-radius: 5px;
                border: none;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";  /* Slightly darker blue on hover */
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        # self.message_input.returnPressed.connect(self.send_message)




        bottom_layout.addWidget(self.send_button)

        # Add bottom layout to main layout
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)
        self.display_new_messages()
    def change_status_handler(self, new_status):
        '''Checking and updating the online status of the seller'''
        print("handler running")
        if new_status:
            self.is_online = True
            self.message_input.setReadOnly(False)
            self.send_button.setEnabled(True)
        else:
            self.is_online = False
            self.message_input.setReadOnly(True)
            self.send_button.setEnabled(False)

        self.other_user_label.setText(f"👤 {self.other_user_name} {"🟢" if self.is_online else "🔴"}")
            
    def refresh_status(self):
        status_code, _, _ = request("GET", f"{url}/messaging_info/{self.other_user_id}")
        self.change_status_handler(status_code==200)

    def display_new_messages(self):
        if self.other_user_id in chat_data:
            chat_history = chat_data[self.other_user_id]["history"]
            while self.first_undisplayed_message < len(chat_history):

                msg, other_sent, date = chat_history[self.first_undisplayed_message]
                self.display_message(msg, other_sent, date)
                self.first_undisplayed_message += 1

    def send_message(self):
        message = self.message_input.toPlainText()
        if not message: return
        # new_chat_socket = 
        if self.other_user_id not in chat_data:
            chat_data[self.other_user_id] = {"user_id": self.other_user_id,
                                             "username": self.other_user_name,
                                    "socket": socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                                    "history": []}
            status_code, _, json_data = request("GET", f"{url}/messaging_info/{self.other_user_id}")
            if status_code != 200: raise Exception() # TODO
            owner_messaging_info = (json_data["messaging_info"]["ip_addr"], json_data["messaging_info"]["port"])
            chat_data[self.other_user_id]["socket"].connect(owner_messaging_info)
            threading.Thread(target=handle_p2p_con, args=(chat_data[self.other_user_id]["socket"],
                                                                self.other_user_id), daemon=True).start()
        elif chat_data[self.other_user_id]["socket"] is None:
            chat_data[self.other_user_id]["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            status_code, _, json_data = request("GET", f"{url}/messaging_info/{self.other_user_id}")
            if status_code != 200: raise Exception() # TODO
            owner_messaging_info = (json_data["messaging_info"]["ip_addr"], json_data["messaging_info"]["port"])
            chat_data[self.other_user_id]["socket"].connect(owner_messaging_info)
            threading.Thread(target=handle_p2p_con, args=(chat_data[self.other_user_id]["socket"],
                                                                self.other_user_id), daemon=True).start()

        to_send = format_message_response(f"{user_id} {username} {message}").encode()
        chat_data[self.other_user_id]["socket"].sendall(to_send)
        chat_data[self.other_user_id]["history"].append((message, False, datetime.datetime.now()))
        self.display_new_messages()

    def display_message(self, msg, other_sent=False, time=None):
        if time is None:
            time = datetime.datetime.now()
        timestamp = time.strftime("%H:%M")  
        
        formatted_message = (f"<table width='100%'><tr><td style='font-weight:bold;'>"
                             f"<span style='font-size: 30px'>{'You' if not other_sent else self.other_user_name}</span></td></b>"
                             f"<span style='color: black; font-size: 25px; display: block; word-wrap: break-word;'>{msg}</span><br>" 
                             f"<td style='text-align:right; font-size:20px;'>{timestamp}</td></tr>")
        
        self.chat_area.append(formatted_message)
        self.message_input.clear()
        self.chat_area.moveCursor(QTextCursor.End)
    def create_chat_ribbon(self):
        ribbon = QWidget()
        ribbon_layout = QHBoxLayout()

        self.other_user_label = QLabel(f"👤 {self.other_user_name} {"🟢" if self.is_online else "🔴"}")
        self.other_user_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)  # Align text in the middle vertically and horizontally
        self.other_user_label.setStyleSheet("""
            font-size: 40px;
            font-family: 'Arial', sans-serif;
            font-weight: bold;
            color: white;
        """)

        

        ribbon_layout.addWidget(self.other_user_label)

        ribbon.setStyleSheet("""
            background-color: #"""+color_ribbon+""";
            padding: 10px;
        """)
        ribbon.setFixedSize(1800, 90)
        ribbon.setLayout(ribbon_layout)
        return ribbon

class LoginPage(QWidget):
    #initialization
    '''Display of the Login page'''
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique Login") #set window title
        self.setMinimumSize(700, 950)  #set min window size
        self.setStyleSheet("""
            background-color: #"""+product_widget_color+""";
            font-family: 'Arial', sans-serif;
            font-size: 35px;
            color: #333;
        """) #set style for window

        main_layout = QVBoxLayout() #main layout

        container_widget = QWidget(self)  #container for widgets
        container_widget.setFixedSize(600, 1000) #fix container size
        container_layout = QVBoxLayout(container_widget)  #container layout


        #adding logo to top 
        logo_label = QLabel(self)
        logo_pixmap = QPixmap("logo.jpeg")
        logo_label.setPixmap(logo_pixmap.scaled(400, 400, Qt.KeepAspectRatio)) #resize
        logo_label.setAlignment(Qt.AlignCenter) #align

        #welcoming text
        welcome_label = QLabel("Welcome to AUBoutique!", self)
        welcome_label.setStyleSheet("font-size: 45px; font-weight: bold; color: #333;")
        welcome_label.setAlignment(Qt.AlignCenter)

        #adding all widgets to container
        container_layout.addWidget(logo_label)
        container_layout.addWidget(welcome_label)

        #create login form layout
        form_layout = QFormLayout()
        form_layout.setAlignment(Qt.AlignCenter)

        #username field
        self.username_input = QLineEdit(self)
        self.username_input.setFixedHeight(50)
        self.username_input.setPlaceholderText("Enter Username")
        self.username_input.setStyleSheet("font-size: 22px; padding: 10px; color:white; background-color: #"+color_buttons+";")

        username_label = QLabel("Username:", self)
        username_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(username_label, self.username_input)

        #password field
        self.password_input = QLineEdit(self)
        self.password_input.setFixedHeight(50)
        self.password_input.setPlaceholderText("Enter Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("font-size: 22px; padding: 10px; color:white; background-color: #"+color_buttons+";")

        password_label = QLabel("Password:", self)
        password_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(password_label, self.password_input)


        #login button
        self.login_button = QPushButton("Login", self)
        self.login_button.setStyleSheet("""
            QPushButton{
                background-color: #"""+color_buttons+""";
                color: white;
                font-size: 22px;
                padding: 15px;
                border-radius: 5px;
            }
            QPushButton:hover{
                background-color: #"""+hover_color+""";
            }
        """)
        self.login_button.clicked.connect(self.login)


        #register button
        self.register_button = QPushButton("No Account? Press Here to Register!", self)
        self.register_button.setStyleSheet("""
            color: #"""+color_buttons+""";
            font-size: 20px;
            padding: 12px;
        """)
        self.register_button.clicked.connect(self.go_to_register)

        #adding all widgets to container
        container_layout.addWidget(logo_label) #logo
        container_layout.addWidget(welcome_label) #welcome
        container_layout.addLayout(form_layout) #form layout
        container_layout.addWidget(self.login_button) #login button
        container_layout.addWidget(self.register_button, alignment=Qt.AlignCenter) #register button

        #add container widget to main layout
        main_layout.addWidget(container_widget, alignment=Qt.AlignCenter)

        #set layout for main window
        self.setLayout(main_layout)


    #login data send to server
    '''User logs in with his credentials'''
    def login(self):
        #take input
        entered_username = self.username_input.text()
        password = self.password_input.text()

        if not entered_username or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both Username and Password.") #warn if any box missing
            return


        status, json_data = server_login(entered_username, password) #send request

        #process response
        if status == 200:
            global user_id
            user_id = json_data["user_id"]
            global username
            username = entered_username
            print(username)
            main_window.main_app.top_ribbon.set_username(username)
            main_window.main_app.redirect_to_all_products()
            
            request("POST", f"{url}/messaging_info", {"ip_addr": ip_addr, "port": port, "user_id": user_id})
            threading.Thread(target=chat_connection, args=(chat_receiving_sock,), daemon=True).start()

        else:
            QMessageBox.warning(self, "Login Failed", json_data["message"]) #error message if failed


    def go_to_register(self):
        main_window.main_app.redirect_to_register()
        # print("Redirecting to Registration page...")
        # self.registration_page = RegisterPage()
        # self.registration_page.show()
        # self.close() #close login page

class RegisterPage(QWidget):
    '''In case you're a new user, make an account'''
    #initialization
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AUBoutique Registration") #set window title
        self.setMinimumSize(700, 950)  #set min window size
        self.setStyleSheet("""
            background-color: #f0f0f0;
            font-family: 'Arial', sans-serif;
            font-size: 24px;
            color: #333;
        """) #set style for window

        main_layout = QVBoxLayout() #main layout

        container_widget = QWidget(self)  #container for widgets
        container_widget.setFixedSize(600, 900) #fix container size
        container_layout = QVBoxLayout(container_widget)  #container layout


        #adding logo to top 
        logo_label = QLabel(self)
        logo_pixmap = QPixmap("/home/mohamad/Documents/VSCode Workspace/EECE_project/phase2/new_version (1)/logo.jpeg")
        logo_label.setPixmap(logo_pixmap.scaled(400, 400, Qt.KeepAspectRatio)) #resize
        logo_label.setAlignment(Qt.AlignCenter) #align

        #welcoming text
        welcome_label = QLabel("Welcome to AUBoutique!", self)
        welcome_label.setStyleSheet("font-size: 45px; font-weight: bold; color: #333; background-color: #"+product_widget_color+";")
        welcome_label.setAlignment(Qt.AlignCenter)

        #adding all widgets to container
        container_layout.addWidget(logo_label)
        container_layout.addWidget(welcome_label)

        #create login form layout
        form_layout = QFormLayout()

        #user data fields
        self.fullname_input = QLineEdit(self)
        self.email_input = QLineEdit(self)
        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)

        #placeholders
        self.fullname_input.setPlaceholderText("Enter Full Name")
        self.email_input.setPlaceholderText("Enter Email Address")
        self.username_input.setPlaceholderText("Choose Username")
        self.password_input.setPlaceholderText("Choose a Password")

        #styling
        self.fullname_input.setStyleSheet("font-size: 22px; padding: 10px; background-color: #"+color_buttons+"; color:white;")
        self.email_input.setStyleSheet("font-size: 22px; padding: 10px; background-color: #"+color_buttons+"; color:white;")
        self.username_input.setStyleSheet("font-size: 22px; padding: 10px; background-color: #"+color_buttons+"; color:white;")
        self.password_input.setStyleSheet("font-size: 22px; padding: 10px; background-color: #"+color_buttons+"; color:white;")

        #continue name field
        name_label = QLabel("Full Name:", self.fullname_input)
        name_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(name_label, self.fullname_input)

        #continue email field
        email_label = QLabel("Email:", self.email_input)
        email_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(email_label, self.email_input)

        #continue username field
        username_label = QLabel("Username:", self.username_input)
        username_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(username_label, self.username_input)

        #continue paaswd field
        password_label = QLabel("Password:", self.password_input)
        password_label.setStyleSheet("font-size: 26px; font-weight: bold;")
        form_layout.addRow(password_label, self.password_input)

        empty_label = QLabel("")
        form_layout.addRow(empty_label)


        pass_needs = QLabel("Password must be at least of 8 Characters and contains")
        pass_needs2 = QLabel("lower case and upper case letters, and special character")
        pass_needs.setStyleSheet("font-size: 19px; font-weight: bold;")
        pass_needs2.setStyleSheet("font-size: 19px; font-weight: bold;")
        form_layout.addRow(pass_needs)
        form_layout.addRow(pass_needs2)


        #register Button
        self.register_button = QPushButton("Register", self)
        self.register_button.setStyleSheet("""
            background-color: #"""+color_buttons+""";
            color: white;
            font-size: 22px;
            padding: 15px;
            border-radius: 5px;
        """)
        self.register_button.clicked.connect(self.register)

        self.login_button = QPushButton("Have an Account? Press Here to Login!", self)
        self.login_button.setStyleSheet("""
            color: #"""+color_buttons+""";
            font-size: 20px;
            padding: 12px;
        """)
        self.login_button.clicked.connect(self.go_to_login)

        #adding all widgets to container
        container_layout.addWidget(logo_label) #logo
        container_layout.addWidget(welcome_label) #welcome
        container_layout.addLayout(form_layout) #form layout
        container_layout.addWidget(self.register_button, alignment=Qt.AlignCenter) #register button
        container_layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

        #add container widget to main layout
        main_layout.addWidget(container_widget, alignment=Qt.AlignCenter)

        #set layout for main window
        self.setLayout(main_layout)

    def go_to_login(self):
        main_window.main_app.redirect_to_login()

    #register data send to server
    def register(self):
        #take input
        fullname = self.fullname_input.text()
        email = self.email_input.text()
        entered_username = self.username_input.text()
        password = self.password_input.text()

        #check for missing areas
        if not fullname or not email or not entered_username or not password:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        #prepare data
        request_data = {
            "action": "register",
            "fullname": fullname,
            "email": email,
            "username": entered_username,
            "password": password
        }

        status_code, json_data = server_register(fullname, entered_username, email, password)

        #process response
        if status_code == 200:
            global user_id, username
            user_id = json_data["user_id"]
            username = entered_username
            main_window.main_app.top_ribbon.set_username(username)
            main_window.main_app.redirect_to_all_products()
            
            request("POST", f"{url}/messaging_info", {"ip_addr": ip_addr, "port": port, "user_id": user_id})
            threading.Thread(target=chat_connection, args=(chat_receiving_sock,), daemon=True).start()
        else:
            QMessageBox.warning(self, "Login Failed", json_data["message"]) #error message if failed

class BoughtProductsPage(QWidget):
    '''User can view the products he/she has purchased'''
    def __init__(self, products):
        super().__init__()
        self.products = products
        self.init_ui()

    def init_ui(self):
        # Main Layout for the page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title for the page
        title = QLabel("Bought Products")
        title.setStyleSheet("""
            font-size: 45px;
            font-weight: bold;
            color: #2C2F38;
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Scroll Area for the product list
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(f"""
            background-color: #"""+back_color+""";
            border: no border;
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(1500)
        scroll_area.setAlignment(Qt.AlignTop)

        # Container widget for the products
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(20)  # Space between products

        # Add products to the layout
        for product in self.products:
            product_widget = self.create_product_widget(product)
            container_layout.addWidget(product_widget)

        # Center the product grid horizontally
        container_layout.setAlignment(Qt.AlignCenter)

        container.setFixedWidth(1475)  # Ensure the container fills the scroll area width
        # product_widget.setFixedWidth(1500)  # Make each product widget fill the container width


        # Set container layout
        container.setLayout(container_layout)
        scroll_area.setWidget(container)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area, alignment=Qt.AlignHCenter)

        # Set main layout to the page
        self.setLayout(main_layout)

    def create_product_widget(self, product):
        # Main widget for a single product
        product_widget = QLabel()
        # product_widget.setFrameShape(QFrame.StyledPanel)
        product_widget.setStyleSheet("""
                background-color: #"""+product_widget_color+""";
                border: no border;
                border-radius: 10px;
        """)
        product_widget.setFixedWidth(1400)
        product_widget.setFixedHeight(300)  # Increased height for better spacing
        product_layout = QHBoxLayout()
        product_layout.setContentsMargins(20, 20, 20, 20)

        # Left: Product Image (Using the provided image-handling logic)
        image_container = QFrame()
        image_container.setFixedSize(200, 200)
        image_container.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 5px;
            }
        """)

        pixmap = QPixmap()
        try:
            if product.get("image"):
                pixmap.loadFromData(base64.b64decode(product["image"]))
            else:
                pixmap.load("path/to/placeholder.png")
        except Exception as e:
            print(f"Error loading image: {e}")
            pixmap.load("path/to/placeholder.png") # these things should be removed

        product_image = QLabel(image_container)
        if not pixmap.isNull():
            # Scale the pixmap to fit within the container
            scaled_pixmap = pixmap.scaled(
                180, 180,  # Slightly smaller than the container
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            product_image.setPixmap(scaled_pixmap)
        else:
            product_image.setText("No Image Available")
            product_image.setStyleSheet("color: #888; font-size: 14px; font-style: italic; background-color: #DCDCDC")

        product_image.setAlignment(Qt.AlignCenter)

        image_layout = QVBoxLayout()
        image_layout.addWidget(product_image)
        image_container.setLayout(image_layout)

        # Add image container to the product layout
        product_layout.addWidget(image_container)

        # Middle: Product Info (Name, Price, and Owner)
        info_container = QFrame()
        info_container.setMaximumWidth(400)
        info_container.setStyleSheet("""
            QFrame {
                background-color: #"""+product_widget_color+""";
                border: none;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setAlignment(Qt.AlignLeft)  # Change this line
        info_layout.setAlignment(Qt.AlignVCenter)

        # Product Name
        product_name = QLabel(product["name"])
        product_name.setStyleSheet("""
            font-size: 35px;
            background-color: #"""+product_widget_color+""";
            font-weight: bold;
            color: #2C2F38;
        """)
        product_name.setAlignment(Qt.AlignLeft)  # Change alignment to left

        # Price
        price_label = QLabel(f"Price: {format_price(product["price"], product["currency"])}")
        price_label.setStyleSheet("""
            font-size: 35px;
            font-weight: bold;
            color: #333;
            background-color: #"""+product_widget_color+""";
        """)
        price_label.setAlignment(Qt.AlignLeft)  # Change alignment to left

        # Owner
        '''Icon and the name of the owner of the product'''
        owner_label = QLabel(f"👤 Owner: {product['owner_name']}")
        owner_label.setStyleSheet("""
            font-size: 35px;
            color: #555;
            background-color: #"""+product_widget_color+""";
        """)
        owner_label.setAlignment(Qt.AlignLeft)  # Change alignment to left

        info_layout.addWidget(product_name)
        info_layout.addWidget(price_label)
        info_layout.addWidget(owner_label)
        info_container.setLayout(info_layout)


        # Add info container to the product layout
        product_layout.addWidget(info_container)

                # Right: Rating Input
        # Right: Rating Input
        rating_container = QFrame()
        rating_container.setFixedWidth(400)
        rating_container.setStyleSheet("""
            QFrame {
                background-color: #"""+product_widget_color+""";
                border: none;
            }
        """)
        rating_layout = QVBoxLayout()
        rating_layout.setAlignment(Qt.AlignCenter)

        # Add StarRatingWidget
        star_rating_widget = StarRatingWidget(product["id"], product["name"])
        rating_layout.addWidget(star_rating_widget)

        rating_container.setLayout(rating_layout)

        # Add rating container to the product layout
        product_layout.addWidget(rating_container, alignment=Qt.AlignRight)


        product_widget.setLayout(product_layout)
        return product_widget
    
    def update_stars(self, index):
        """Fill the stars up to the selected index."""
        for i, star in enumerate(self.stars):
            if i <= index:
                star.setText("★")  # Filled star
            else:
                star.setText("☆")  # Empty star
        self.current_rating = index + 1

class StarRatingWidget(QWidget):
    '''Users can rate products as well as view the ratings of products'''
    def __init__(self, product_id, product_name):
        super().__init__()
        self.current_rating = 0
        self.product_id = product_id
        self.product_name = product_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Star Buttons Layout
        self.stars = []
        star_layout = QHBoxLayout()
        star_layout.setSpacing(5)

        for i in range(5):
            star_button = QPushButton("☆")
            star_button.setFixedSize(50, 50)
            star_button.setStyleSheet("""
                QPushButton {
                    font-size: 36px;
                    color: #FFD700;  /* Gold color for stars */
                    border: none;
                    background: #"""+product_widget_color+""";
                }
                QPushButton:hover {
                    color: #FFA500;  /* Orange color on hover */
                }
            """)
            star_button.clicked.connect(lambda checked, idx=i: self.update_stars(idx))
            self.stars.append(star_button)
            star_layout.addWidget(star_button)

        layout.addLayout(star_layout)

        # Submit Button
        submit_button = QPushButton("Submit Rating")
        submit_button.setFixedSize(150, 40)
        submit_button.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                color: white;  /* Green color */
                border: 1px solid #4CAF50;
                border-radius: 5px;
                background-color: #"""+color_buttons+""";
            }
            QPushButton:hover {
                background-color: #"""+hover_color+""";
                color: white;
            }
        """)
        submit_button.clicked.connect(self.submit_rating)
        layout.addWidget(submit_button, alignment=Qt.AlignCenter)

        self.setLayout(layout)

    def update_stars(self, index):
        """Fill the stars up to the selected index."""
        for i, star in enumerate(self.stars):
            if i <= index:
                star.setText("★")  # Filled star
            else:
                star.setText("☆")  # Empty star
        self.current_rating = index + 1

    def submit_rating(self):
        """Submit the current rating."""
        status_code, json_data = server_add_rating(user_id, self.current_rating, self.product_id)
        if status_code == 200:
            main_window.add_notification("Rating Submitted", f"Rating submitted successfully: {self.current_rating}/5 for {self.product_name}")

class MyBoughtProductsPage(QWidget):
    '''Users can view their products that have been sold'''
    def __init__(self, products):
        super().__init__()
        self.products = products
        self.init_ui()

    def init_ui(self):
        # Main Layout for the page
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title for the page
        title = QLabel("Sold Products")
        title.setStyleSheet("""
            font-size: 45px;
            font-weight: bold;
            color: #2C2F38;
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Scroll Area for the product list
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet(f"""
            background-color: #"""+back_color+""";
            border: no border;
        """)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedWidth(1500)
        scroll_area.setAlignment(Qt.AlignTop)

        # Container widget for the products
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setSpacing(20)  # Space between products

        # Add products to the layout
        for product in self.products:
            for transaction in product["transactions"]:
                data = product.copy()
                for key, value in transaction.items():
                    data[key] = value
                product_widget = self.create_product_widget(data)
                product_widget.setFixedWidth(1400)  # Make each product widget fill the container width
                container_layout.addWidget(product_widget)

        # Center the product grid horizontally
        container_layout.setAlignment(Qt.AlignCenter)

        container.setFixedWidth(1475)  # Ensure the container fills the scroll area width
        # product_widget


        # Set container layout
        container.setLayout(container_layout)
        scroll_area.setWidget(container)

        # Add scroll area to the main layout
        main_layout.addWidget(scroll_area, alignment=Qt.AlignHCenter)

        # Set main layout to the page
        self.setLayout(main_layout)

    def create_product_widget(self, product):
        # Main widget for a single product
        product_widget = QFrame()
        product_widget.setFrameShape(QFrame.StyledPanel)
        product_widget.setStyleSheet("""
            QFrame {
                background-color: #"""+product_widget_color+""";
                border: no border;
                border-radius: 10px;
            }
        """)
        product_widget.setFixedWidth(800)
        product_widget.setFixedHeight(300)  # Increased height for better spacing
        product_layout = QHBoxLayout()
        product_layout.setContentsMargins(20, 20, 20, 20)

        # Left: Product Image (Using the provided image-handling logic)
        image_container = QFrame()
        image_container.setFixedSize(200, 200)
        image_container.setStyleSheet("""
            QFrame {
                background-color: #DCDCDC;
                border-radius: 5px;
            }
        """)

        pixmap = QPixmap()
        try:
            if product.get("image"):
                pixmap.loadFromData(base64.b64decode(product["image"]))
            else:
                pixmap.load("path/to/placeholder.png")
        except Exception as e:
            print(f"Error loading image: {e}")
            pixmap.load("path/to/placeholder.png") # these things should be removed

        product_image = QLabel(image_container)
        if not pixmap.isNull():
            # Scale the pixmap to fit within the container
            scaled_pixmap = pixmap.scaled(
                180, 180,  # Slightly smaller than the container
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            product_image.setPixmap(scaled_pixmap)
        else:
            product_image.setText("No Image Available")
            product_image.setStyleSheet("color: #888; font-size: 14px; font-style: italic; background-color: #DCDCDC")

        product_image.setAlignment(Qt.AlignCenter)

        image_layout = QVBoxLayout()
        image_layout.addWidget(product_image)
        image_container.setLayout(image_layout)

        # Add image container to the product layout
        product_layout.addWidget(image_container)

        # Middle: Product Info (Name, Price, and Owner)
        info_container = QFrame()
        info_container.setMaximumWidth(400)
        info_container.setStyleSheet("""
            QFrame {
                background-color: #"""+product_widget_color+""";
                border: none;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(5, 5, 5, 5)
        info_layout.setAlignment(Qt.AlignLeft)  # Change this line
        info_layout.setAlignment(Qt.AlignVCenter)

        # Product Name
        product_name = QLabel(product["name"])
        product_name.setStyleSheet("""
            font-size: 35px;
            background-color: #"""+product_widget_color+""";
            font-weight: bold;
            color: #2C2F38;
        """)
        product_name.setAlignment(Qt.AlignLeft)  # Change alignment to left

        # Price
        price_label = QLabel(f"Price: {format_price(product["price"], product["currency"])}")
        price_label.setStyleSheet("""
            font-size: 35px;
            font-weight: bold;
            color: #333;
            background-color: #"""+product_widget_color+""";
        """)
        price_label.setAlignment(Qt.AlignLeft)  # Change alignment to left

        # Price
        quantity_label = QLabel(f"Quantity: {product["quantity"]}")
        quantity_label.setStyleSheet("""
            font-size: 35px;
            font-weight: bold;
            color: #333;
            background-color: #"""+product_widget_color+""";
        """)
        quantity_label.setAlignment(Qt.AlignLeft)  # Change alignment to left

        # Owner
        buyer_label = QLabel(f"👤 Buyer: {product['buyer_username']}") #HH
        
        buyer_label.setCursor(Qt.PointingHandCursor)
        buyer_label.setStyleSheet("""
            QLabel {
                font-size: 35px;
                font-weight: bold;
                color: #555;
                background-color: #""" + product_widget_color + """;
            }
            QLabel:hover {
                text-decoration: underline;  /* Add underline on hover for indication */
                color: black;
            }
        """)
        buyer_label.setAlignment(Qt.AlignLeft)  # Change alignment to left
        buyer_label.mousePressEvent = lambda _: main_window.main_app.redirect_to_owner(product["buyer_id"], product["buyer_name"])

        info_layout.addWidget(product_name)
        info_layout.addWidget(price_label)
        info_layout.addWidget(quantity_label)
        info_layout.addWidget(buyer_label)
        info_container.setLayout(info_layout)


        # Add info container to the product layout
        product_layout.addWidget(info_container)

        '''       # Right: Rating Input
        # Right: Rating Input
        rating_container = QFrame()
        rating_container.setFixedWidth(400)
        rating_container.setStyleSheet("""
            QFrame {
                background-color: #"""+product_widget_color+""";
                border: none;
            }
        """)
        rating_layout = QVBoxLayout()
        rating_layout.setAlignment(Qt.AlignCenter)

        # Add StarRatingWidget
        star_rating_widget = StarRatingWidget(product["id"], product["name"])
        rating_layout.addWidget(star_rating_widget)

        rating_container.setLayout(rating_layout)

        # Add rating container to the product layout
        product_layout.addWidget(rating_container, alignment=Qt.AlignRight)'''

        # product_widget.setFixedSize(100, 100)
        product_widget.setLayout(product_layout)
        return product_widget

def request(method, url, json_data=None):
    #call both functions to complete the whole thing
    response = send_http_request(method, url, json_data)
    status_code, headers, json_data = parse_http_resp(response)

    #return needed info
    print("received response")
    return status_code, headers, json_data

def send_http_request(method, url, json_data=None):

    #host - port - path
    host = 'localhost'
    path = '/' + url.split('localhost')[-1].split('/', 1)[-1]

    #create the string for request
    if json_data:
        body = json.dumps(json_data)
    else:
        body = ""

    request = (
        f"{method} {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Connection: keep-alive\r\n\r\n"
        f"{body}"
    )

    #sending request
    server_sock.sendall(request.encode('utf-8'))

    #receive response
    response = b""
    while b"\r\n\r\n" not in response:
        app.processEvents()
        part = server_sock.recv(4096)
        response += part
    
    headers, body = response.split(b"\r\n\r\n", 1)
    content_length = int([line.split(b": ")[1] for line in headers.split(b"\r\n") if b"Content-Length" in line][0])
    
    while len(body) < content_length:
        body += server_sock.recv(min(4096, content_length - len(body)))
    
    #return the response
    resp = headers.decode('utf-8') + "\r\n\r\n" + body.decode('utf-8')
    return resp

def parse_http_resp(response):
    
    app.processEvents()
    #extract headers and body from each other
    headers, body = response.split("\r\n\r\n", 1)
    header_lines = headers.split("\r\n")

    #parse status line --it's the fist line of headers
    status_line = header_lines[0].split()
    status_code = int(status_line[1])

    #parsing the headers
    response_headers = {}
    for line in header_lines[1:]:
        key, value = line.split(": ",1)
        response_headers[key] = value
        app.processEvents()
    #if there's json --> parse body as json
    json_checker = response_headers.get('Content-Type', '')
    if 'application/json' in json_checker:
        json_data = json.loads(body)
    
    return status_code, response_headers, json_data

def server_register(name, username, email, password):
    status_code, _, json_data = request("POST", f"{url}/register", json_data={"name": name, "username": username,
                                                                              "email_address": email, "password": password})
    return status_code, json_data

def server_login(username, password):
    status_code, _, json_data = request("POST", f"{url}/login", json_data={"username": username, "password": password})
    return status_code, json_data   

def server_get_bestseller_products():
    status_code, _, json_data = request("GET", f"{url}/most_sold?currency={chosen_currency}")
    return status_code, json_data

def server_add_product(name, image_path, price, currency, desc, quantity):
    global user_id
    with open(image_path, 'rb') as f:
        image = f.read()
    i = image_path.rfind('.')
    ext = image_path[i:]
    product_data = {
        "name": name, 
        "image": {"content": base64.b64encode(image).decode(), "extension": ext},
        "price": price, 
        "currency": currency,
        "description": desc,
        "quantity": quantity,
        "user_id": user_id
    }
    
    return request("POST", f"{url}/products", product_data)

def server_get_all_products():
    status_code, _, json_data = request("GET", f"{url}/products?currency={chosen_currency}")
    return status_code, json_data

def server_get_owner_products(owner_id):
    return request("GET", f"{url}/products/{owner_id}?currency={chosen_currency}")

def server_buy_product(product_id, quantity):
    json_data = {"user_id": user_id, "product_id": product_id, "quantity": quantity}
    status_code, _, json_data = request("POST", f"{url}/buy_product", json_data=json_data)
    return status_code, json_data

def server_get_my_products(user_id):
    status_code, _, json_data = request("GET", f"{url}/my_products/{user_id}?currency={chosen_currency}")
    return status_code, json_data

def server_get_product_info(product_id):
    status_code, _, json_data = request("GET", f"{url}/product/{product_id}?currency={chosen_currency}")
    return status_code, json_data

def chat_connection(chat_receiving_sock):
    chat_receiving_sock.listen()
    while True:
        other_end_sock, _ = chat_receiving_sock.accept()
        threading.Thread(target=handle_p2p_con, args=(other_end_sock,), daemon=True).start()

def handle_p2p_con(other_end_sock, other_user_id=None):
    while True:
        try:
            length = int(other_end_sock.recv(4))
        except ConnectionResetError:
            if other_user_id in chat_data:
                chat_data[other_user_id]["socket"] = None
            cur_page = main_window.main_app.page_stack.currentWidget()
            if isinstance(cur_page, ChatWindow) and cur_page.other_user_id == other_user_id:
                # cur_page.emit_offline()
                cur_page.emit_change_status(False)
                
            return
        raw_msg = other_end_sock.recv(length).decode()
        sender_id, sender_username, msg = raw_msg.split(' ', 2)
        sender_id = int(sender_id)
        # print(msg)
        if other_user_id is None:
            other_user_id = sender_id
        else:
            if sender_id != other_user_id: raise Exception() # TODO
        if sender_id not in chat_data:
            chat_data[sender_id] = {"user_id": sender_id,
                                             "username": sender_username,
                                    "socket": other_end_sock,
                                    "history": []}
        else:
            chat_data[sender_id]["socket"] = other_end_sock

        cur_page = main_window.main_app.page_stack.currentWidget()

        chat_data[sender_id]["history"].append((msg, True, datetime.datetime.now()))
        if isinstance(cur_page, ChatWindow) and cur_page.other_user_id == sender_id:
            cur_page.emit_new_message_signal()
            cur_page.emit_change_status(True)
        else:
            main_window.new_message(chat_data[other_user_id]["username"])

def format_message_response(to_send):
    """Format messaging according to our chatting protocol"""
    length = str(len(to_send)).rjust(3, '0')
    return length + " " + to_send

def server_get_bought_products(user_id):
    status_code, _, json_data = request("GET",
                                        f"{url}/bought_products?user_id={user_id}&currency={chosen_currency}")
    return status_code, json_data

def server_add_rating(user_id, rating, product_id):
    
    status_code, _, json_data = request("POST", f"{url}/rating",
            json_data={"user_id": user_id, "rating": rating, "product_id": product_id})
    return status_code, json_data   

def server_search(query):
    status_code, _, json_data = request("GET", f"{url}/search?q={query}&currency={chosen_currency}")
    return status_code, json_data

chat_data = {} 
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.connect(('localhost', 9999))

chat_receiving_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
chat_receiving_sock.bind(('localhost', 0))
ip_addr, port = chat_receiving_sock.getsockname()

user_id = None
username = None

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
app = QApplication(sys.argv)
WINDOW_SIZE = (app.primaryScreen().size().width(), app.primaryScreen().size().height())
main_window = MainWindow()
main_window.setWindowFlags(main_window.windowFlags() & ~Qt.WindowMinMaxButtonsHint)
main_window.set_up_ui()
main_window.showMaximized()
sys.exit(app.exec_())