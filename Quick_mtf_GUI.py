import sys,os,csv
import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QFileDialog,QGraphicsTextItem,QGraphicsEllipseItem
from PyQt5.QtGui import QPixmap, QImage, QPen,QFont,QPainter
from PyQt5.QtCore import Qt, QRectF
from ui_MainWindow import Ui_MainWindow
from quickMTF.quickMTF import quickMTF
import matplotlib.pyplot as plt
class GraphicsSceneWithDrawing(QGraphicsScene):
    def __init__(self, main_window, image_path):
        super().__init__()
        self.main_window = main_window
        self.image_path = image_path
        self.drawing = False
        self.start_pos = None
        self.rect_item = None
        self.x = 0
        self.y = 0
        self.width, self.height = 0, 0
        self.data = []
        self.pen = QPen(Qt.blue, 1)  # Red pen with 2-pixel width
        self.pixmap_item = None  # To store the current pixmap item
        self.counter = 0  # Counter for rectangles
        self.rectangles_with_text = []  # List to store rectangles and their text items
        self.text_items_list = []
        self.rectangles_list = []  # List to store drawn rectangles
        self.html_shown = True



    def mousePressEvent(self, event):
        # Set the drawing flag to True and store the start position when the mouse is pressed
        if not self.html_shown:
            self.drawing = True
            self.start_pos = event.scenePos()

    def mouseMoveEvent(self, event):
        # If drawing flag is True, update the rectangle size and position
        if not self.html_shown:
            if self.drawing and self.start_pos:
                current_pos = event.scenePos()
                self.draw_rectangle(self.start_pos, current_pos)
                self.data = []

    def mouseReleaseEvent(self, event):
        # Reset the drawing flag to False when the mouse is released
        if not self.html_shown:
            self.data = (int(self.x), int(self.y), int(self.width), int(self.height))
            self.counter += 1
            #print(self.data)
            # Log the saved image path with timestamp
            self.main_window.log_message(f"Cropped image coordinates No.{self.counter}: {self.data}")
            self.drawing = False
            self.start_pos = None
            self.rect_item = None

            self.main_window.log_message(f"done crop:{self.counter}")
            a,b,c,d,d2,d3=self.main_window.save_cropped_image()
            # Create a QGraphicsTextItem
            if d3==1:
                text_item = QGraphicsTextItem(
                    f" {self.counter}__{int(self.x)},{int(self.y)}\nMTF:{a} \n {d2}pixel/pair \n horizontal:{self.main_window.flip}")
            else:
                if a <0:
                    text_item = QGraphicsTextItem(
                        f" {self.counter}__{int(self.x)},{int(self.y)}\n not slant edge ")
                else:
                    text_item  = QGraphicsTextItem(f" {self.counter}__{int(self.x)},{int(self.y)}\nMTF{d2}:{a} c/p \n angle:{b} ")
            text_item .setFont(QFont("Arial", 10))  # Set the font and size
            # Set the color of the text to red
            text_item .setDefaultTextColor(Qt.red)

            # Set the position of the text item
            text_item.setPos(int(self.x)-90, int(self.y))  # Adjust the (x, y) coordinates to set the position

            # Add the text item to the scene
            self.addItem(text_item )
            # Add the text item to the list
            self.text_items_list.append(text_item)

            self.main_window.update_lcd_number()
            self.main_window.show_plots = 0

    def draw_rectangle(self, start_pos, end_pos):
        # Draw a rectangle using the start position and current position
        if self.rect_item:
            self.removeItem(self.rect_item)

        rect = self.get_rectangle_from_points(start_pos, end_pos)
        self.rect_item = self.addRect(rect, self.pen)
        # Add the rectangle to the list
        self.rectangles_list.append(self.rect_item)



    def get_rectangle_from_points(self, start_pos, end_pos):
        # Create a QRectF object from the given points
        self.x = min(start_pos.x(), end_pos.x())
        self.y = min(start_pos.y(), end_pos.y())
        self.width = abs(start_pos.x() - end_pos.x())
        self.height = abs(start_pos.y() - end_pos.y())
        return QRectF(self.x, self.y, self.width, self.height)



    def clear_rectangles(self):
        self.blockSignals(True)

        # Remove all drawn rectangles from the scene
        for rect_item in self.rectangles_list:
            self.removeItem(rect_item)

        # Remove all text items from the scene
        for text_item in self.text_items_list:
            self.removeItem(text_item)

        # Clear the lists
        self.rectangles_list.clear()
        self.text_items_list.clear()

        # Reset the counter
        self.counter = 0

        # Log the action with timestamp
        self.main_window.log_message("All rectangles and text items cleared.")

    def redo_rectangles(self):
        # Remove the last drawn rectangle from the scene
        self.main_window.log_message(f" Total rectangles: {self.counter}")
        if self.rectangles_list:
            last_rect_item = self.rectangles_list.pop()  # Remove the last rectangle from the list
            self.removeItem(last_rect_item)
            self.counter -= 1
        if self.text_items_list:
            last_text_item = self.text_items_list.pop()  # Remove the last text item from the list
            self.removeItem(last_text_item)

            # Log the action with timestamp
            self.main_window.log_message(f"Last drawn rectangle removed. Total rectangles: {self.counter}")

    def save_image_with_rectangles_and_text(self, file_path):
        # Create a new QPixmap with the size of the scene
        pixmap = QPixmap(self.sceneRect().size().toSize())

        # Create a QPainter to draw on the pixmap
        painter = QPainter(pixmap)

        # Render the scene onto the pixmap
        self.render(painter)

        # End painting
        painter.end()

        # Save the pixmap to the specified file path
        pixmap.save(file_path)



class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create an instance of the generated UI class
        self.window = Ui_MainWindow()
        self.window.setupUi(self)

        self.scene = GraphicsSceneWithDrawing(self, image_path=None)
        self.window.graphicsView.setScene(self.scene)



        self.log_messages = []
        # Connect the valueChanged signal of the horizontalSlider to the zoom_slot
        self.window.horizontalSlider.valueChanged.connect(self.zoom_slot)
        self.window.verticalSlider.valueChanged.connect(self.MTF_slot)
        self.window.lcdNumber.display(self.scene.counter)  # Display the initial value
        # Initial zoom level (100%)
        self.zoom_factor = 1.0
        self.update_zoom_label()
        self.image_paths = []  # List to store the paths of the loaded image files
        self.current_index = 0  # Index of the currently displayed image in the list

        # Connect your own slots or signals here
        self.window.pushButton.clicked.connect(self.load_images)
        self.window.pushButton_10.clicked.connect(self.clear_imageslist)
        self.window.pushButton_9.clicked.connect(self.next_image)
        self.window.listWidget_2.itemClicked.connect(self.list_item_clicked)
        self.window.pushButton_3.clicked.connect(self.clear_rectangles)
        self.window.pushButton_4.clicked.connect(self.save_all_logs_to_file)
        self.window.pushButton_2.clicked.connect(self.save_image)
        self.window.pushButton_5.clicked.connect(self.destroy_plots)
        self.window.pushButton_6.clicked.connect(self.redo_rectangles)
        self.window.pushButton_7.clicked.connect(self.save_to_csv)
        self.window.pushButton_8.clicked.connect(self.save_all_images)
        # Connect the combobox signal to a slot
        self.window.comboBox.currentIndexChanged.connect(self.on_combo_box_changed)
        self.window.actionHelp.triggered.connect(self.display_bb_html_file)
        self.window.actionQuick_MTF.triggered.connect(self.close_html_file)
        self.window.actionClear_All.triggered.connect(self.clear_rectangles)
        # Connect the valueChanged signal of spinBox_percentage to update_circle_radius slot
        self.window.spinBox.valueChanged.connect(self.update_circle_radius)
        self.window.pushButton_11.clicked.connect(self.toggle_circle_visibility)
        self.is_circle_visible = False
        self.percentage_text_item = QGraphicsTextItem()
        self.percentage_text_item.setDefaultTextColor(Qt.red)
        self.percentage_text_item.setFont(QFont("Arial", 12))
        self.percentage_text_item.setPos(10, 10)  # Set the position of the text item

        self.test=quickMTF()
        self.mtf_indx = 30
        self.mtf = 0
        self.show_plots = 0
        self.selected_index=2
        self.flip=False


    def toggle_circle_visibility(self):
        if self.is_circle_visible:
            # If circle is visible, remove it from the scene
            for item in self.scene.items():
                if isinstance(item, QGraphicsEllipseItem):
                    self.scene.removeItem(item)
            # Change the button text to "Show Circle" since the circle is now hidden
            self.scene.removeItem(self.percentage_text_item)
            self.window.pushButton_11.setText("Show Circle")
            self.is_circle_visible = False
        else:
            # If circle is not visible, show it on the scene
            self.update_circle_radius()
            # Add the percentage text item back to the scene
            self.scene.addItem(self.percentage_text_item)
            # Change the button text to "Hide Circle" since the circle is now shown
            self.window.pushButton_11.setText("Hide Circle")
            self.is_circle_visible = True

    def update_circle_radius(self):
        # Get the size of the loaded image
        if self.scene.image_path is None:
            # If no image is loaded, return without updating the circle
            return

        image = QImage(self.scene.image_path)
        image_width = image.width()
        image_height = image.height()


        # Calculate the percentage value from the spinBox
        self.circle_radius_percentage = self.window.spinBox.value()

        # Calculate the radius of the circle based on the percentage of the smaller dimension
        circle_radius = min(image_width, image_height) * self.circle_radius_percentage / 100

        # Calculate the position of the circle's center (same as before)
        circle_center_x = image_width / 2
        circle_center_y = image_height / 2

        # Remove any existing circle item from the scene
        for item in self.scene.items():
            if isinstance(item, QGraphicsEllipseItem):
                self.scene.removeItem(item)

        # Ensure that the circle remains within the image boundaries
        x = max(0, circle_center_x - circle_radius)
        y = max(0, circle_center_y - circle_radius)
        width = min(image_width - x, circle_radius * 2)
        height = min(image_height - y, circle_radius * 2)

        # Create an instance of QGraphicsEllipseItem representing the circle
        circle_item = QGraphicsEllipseItem(x, y, width, height)

        # Set the appearance of the circle (pen and brush)
        pen = QPen(Qt.blue, 2)
        circle_item.setPen(pen)


        # Add the circle to the QGraphicsScene
        self.scene.addItem(circle_item)
        self.update_percentage_text(self.circle_radius_percentage)

    def update_percentage_text(self, percentage):
        # Update the text of the percentage text item
        self.percentage_text_item.setPlainText(f"Percentage: {percentage:.2f}%")
    def display_bb_html_file(self):
        # Assuming "bb.html" is in the same directory as the script
        self.log_message("show help")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "doc","sfr.png")

        if os.path.isfile(file_path):
            self.display_html_file(file_path)

    def display_html_file(self, file_path):
        pixmap = QPixmap(file_path)
        pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.clear()
        self.scene.addItem(pixmap_item)

    def close_html_file(self):
        # Close the HTML file and set the html_shown flag to False
        self.scene.clear()
        self.scene.html_shown = False



    def on_combo_box_changed(self):
        # Get the currently selected item's index
        self.selected_index = (self.window.comboBox.currentIndex()+1)*2
        # Get the currently selected item's text
        selected_text = self.window.comboBox.currentText()
        self.log_message(f"Selected Index: {self.selected_index}, Selected Text: {selected_text}")
        # Update the label with the selected item's information
        #self.label.setText(f"Selected Index: {selected_index}, Selected Text: {selected_text}")

    def load_images(self):
        options = QFileDialog.Options()
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Open Images", "", "Images (*.png *.jpg *.bmp *.gif)",
                                                     options=options)
        if file_paths:
            self.image_paths = file_paths
            self.current_index = 0
            self.update_list_widget()
            self.display_image()
            self.scene.html_shown = False


    def next_image(self):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.update_list_widget()
            self.display_image()

    def list_item_clicked(self, item):
        index = self.window.listWidget_2.row(item)
        if 0 <= index < len(self.image_paths):
            self.current_index = index
            self.display_image()

    def update_list_widget(self):
        self.window.listWidget_2.clear()
        for path in self.image_paths:
            file_name = path.split("/")[-1]  # Get only the file name without the path
            self.window.listWidget_2.addItem(file_name)

    def display_image(self):
        if self.image_paths:
            file_path = self.image_paths[self.current_index]
            pixmap = QPixmap(file_path)
            self.scene.clear()
            pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(pixmap_item)
            #
            # # Fit the image in the view
            # self.window.graphicsView.fitInView(pixmap_item, Qt.KeepAspectRatio)

            # Log the file path with timestamp
            self.log_message(file_path)

            # Get the image size
            image = QImage(file_path)

            image_size = f"{image.width()} x {image.height()} pixels"

            # Update the image size label in the ui_MainWindow
            self.window.label_2.setStyleSheet("color: blue; font-size: 15px;")
            self.window.label_2.setText(f"Image Size: {image_size}")

            # Reset the zoom factor to 100% when opening a new image
            self.window.horizontalSlider.setValue(50)
            self.zoom_factor = 1.0
            self.update_zoom()
            self.update_zoom_label()

            # Fit the image in the view
            self.window.graphicsView.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

            # Update the GraphicsSceneWithDrawing instance with the image_path
            self.scene.image_path = file_path
    def clear_imageslist(self):
        selected_row = self.window.listWidget_2.currentRow()
        if selected_row != -1:
            # Remove the currently selected item from listWidget_2
            self.window.listWidget_2.takeItem(selected_row)

            # Update the image_paths list to remove the deleted image
            del self.image_paths[selected_row]

            # If the currently displayed image is the one being deleted, update the display
            if self.current_index == selected_row:
                self.current_index = 0  # Reset the current index to show the first image
                self.display_image()  # Display the first image after deletion

        # Clear the selection in listWidget_2
        self.window.listWidget_2.clearSelection()


        # Clear the currently displayed image in graphicsView_2 (optional, depends on your usage)
        #self.scene_2.clear()


    def save_all_images(self):
        # Prompt the user to select the folder to save the images
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg *.bmp)", options=options)

        if file_path:
            # Iterate through all the rectangles and text items in the scene

            self.scene.save_image_with_rectangles_and_text(file_path)

            # Log the action with timestamp
            self.log_message("All images saved.")

    def update_lcd_number(self):
        # Update the value displayed in the QLCDNumber widget
         self.window.lcdNumber.display(self.scene.counter)
        # Set the foreground color (text color) of the QLCDNumber to red


    def setup_connections(self):
        # Connect the buttons to their respective methods
        self.window.pushButton.clicked.connect(self.open_image)
        self.window.pushButton_3.clicked.connect(self.clear_rectangles)

    def clear_rectangles(self):
        # Call the clear_rectangles method of the GraphicsSceneWithDrawing instance
        self.scene.clear_rectangles()
        self.update_lcd_number()


    def save_image(self):
        pixmap = self.get_image_from_graphics_view()
        if pixmap:
            options = QFileDialog.Options()
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg *.bmp)",
                                                       options=options)
            if file_path:
                pixmap.save(file_path)
                self.log_message(f"Image saved: {file_path}")

    def get_image_from_graphics_view(self):
        # Render the QGraphicsView with all its items onto a QPixmap
        pixmap = QPixmap(self.window.graphicsView.size())
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.scene.render(painter)
        painter.end()
        image = pixmap.toImage()
        return image

    def save_cropped_image(self):
        if self.scene.data:
            x, y, width, height = self.scene.data
            angel=0
            flag=0
            image =plt.imread(self.scene.image_path)
            x = max(0, x)
            y = max(0, y)
            # width = min(width, image.width - x)
            # height = min(height, image.height - y)
            heightC, widthC, _ = image.shape
            width = min(width, widthC - x)
            height = min(height, heightC - y)
            self.window.label_5.setText(f"crop Size: {width}x{height}")


            is_checked1 = self.window.checkBox.isChecked()
            is_checked2 = self.window.checkBox_2.isChecked()
            is_checked3 = self.window.checkBox_3.isChecked()
            is_checked4 = self.window.checkBox_4.isChecked()
            is_checked5 = self.window.checkBox_5.isChecked()
            is_checked6 = self.window.checkBox_6.isChecked()
            is_checked7 = self.window.checkBox_7.isChecked()

            if not is_checked6:
                plotflag=0
                height1 = 150 if height > 150 else height
                self.flip = True if is_checked7 else False
                if is_checked5:
                    plotflag=1
                    plt.clf()
                self.mtf,pp=self.test.linepairMTF_Gui(image, x, y, width, height1, plotflag,self.scene.counter,self.flip,library='cv2')
                self.mtf_indx=pp
                self.window.label_7.setStyleSheet("color: blue; font-size: 15px;")
                self.window.label_7.setText(f"MTF: {self.mtf}")
                self.window.label_6.setText(f"MTF: n/a")
                self.log_message(
                    f"Seq: {self.scene.counter} ;MTF: {self.mtf} ;from:{x},{y}; size:{width}x{height}, {pp} pixel/pair")
                if is_checked5:
                    plt.show()
                flag=1
            else:
                cropped_image = image[y:y + height, x:x + width]
                # cropped_image = image.crop((x, y, x + width, y + height))
                # cwd = os.getcwd()
                # save_path = os.path.join(cwd, "sfr_image.png")
                # cropped_image.save(save_path)
                self.mtf_indx = self.window.verticalSlider.sliderPosition()


                # Use the is_checked value as needed
                if is_checked1:
                    self.log_message("The sfr is checked!")
                    self.show_plots=1

                if is_checked2:
                    self.log_message("The LSF is checked!")
                    self.show_plots=4
                if is_checked3:
                    self.log_message("The edge is checked!")
                    self.show_plots=5
                if is_checked4:
                    self.log_message("The none is checked!")
                    self.show_plots=0
                else:
                    self.log_message("The none is unchecked!")
                #self.mtf, angel ,self.mtf_nyquist= self.test.sfr_GUI("sfr_image.png", self.selected_index,self.scene.counter, float(self.mtf_indx)/100, self.show_plots,return_fig=False)
                self.mtf, angel, self.mtf_nyquist = self.test.sfr_GUI(cropped_image, self.selected_index,
                                                                      self.scene.counter, float(self.mtf_indx) / 100,
                                                                      self.show_plots, return_fig=False)
                self.log_message(f"Seq: {self.scene.counter} ;MTF{self.mtf_indx}: {self.mtf} c/p; Angle:{angel};at:{x},{y}; size:{width}x{height} Nyquist MTF:{self.mtf_nyquist}")
                self.window.label_6.setStyleSheet("color: red; font-size: 15px;")
                self.window.label_6.setText(f"Nyquist MTF:{self.mtf_nyquist}")
                self.window.label_7.setText(f"MTF: n/a")
                # try:
                #     os.remove(save_path)
                # except Exception as e:
                #     self.log_message(f"Error deleting saved image: {save_path}, {e}")
        return self.mtf, angel,width,height,self.mtf_indx,flag


    def update_zoom_label(self):
        # Update the zoom factor label in the ui_MainWindow
        self.window.label_1.setText(f"Zoom: {self.zoom_factor:.2f}")
    def update_mtf_label(self):
        # Update the zoom factor label in the ui_MainWindow
        self.window.label_3.setText(f"MTF: {self.mtf_indx:.1f}")

    def zoom_slot(self, value):
        # Map the value from the slider to the zoom factor (0.5 to 2.0)
        self.zoom_factor = 0.5 + value / 100.0
        self.update_zoom_label()
        # Update the zoom level of the QGraphicsView
        self.update_zoom()

    def MTF_slot(self, value):
        # Map the value from the slider to the zoom factor (0.5 to 2.0)
        self.mtf_indx =  value
        self.update_mtf_label()
        #self.log_message(f"mtf index {value}")
    def redo_rectangles(self):
        # Call the redo_rectangles method of the GraphicsSceneWithDrawing instance
        self.scene.redo_rectangles()


    def update_zoom(self):
        # Set the scale of the QGraphicsView
        self.window.graphicsView.resetTransform()
        self.window.graphicsView.scale(self.zoom_factor, self.zoom_factor)

    def log_message(self, message):
        # Get the current time and date
        current_time = datetime.datetime.now()
        formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        # Log the message with timestamp
        log_message = f"{formatted_time}: {message}"
        self.window.listWidget.addItem(log_message)
        self.log_messages.append(log_message)

    def open_image(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image File", "", "Images (*.png *.jpg *.bmp *.gif)",
                                                   options=options)
        if file_path:
            pixmap = QPixmap(file_path)
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.clear()
            self.scene.addItem(self.pixmap_item)

            # Store the file path in the GraphicsSceneWithDrawing instance
            self.scene.image_path = file_path

            # Log the file path with timestamp
            self.log_message(file_path)

            # Get the image size
            image = QImage(file_path)
            image_size = f"{image.width()} x {image.height()} pixels"

            # Update the image size label in the ui_MainWindow
            self.window.label_2.setText(f"Image Size: {image_size}")

            # Reset the zoom factor to 100% when opening a new image
            self.window.horizontalSlider.setValue(50)
            self.zoom_factor = 1.0
            self.update_zoom()
            self.update_zoom_label()

            # Fit the image in the view
            self.window.graphicsView.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

            # Update the GraphicsSceneWithDrawing instance with the image_path
            self.scene.image_path = file_path

    def save_all_logs_to_file(self):
        # Create the folder if it doesn't exist
        # Prompt the user to select the folder and file name for saving the log messages
        options = QFileDialog.Options()
        folder_path, _ = QFileDialog.getSaveFileName(self, "Save Log File", "", "Text Files (*.txt);;All Files (*)", options=options)

        if folder_path:
            # Open the log file in write mode and write all log messages
            with open(folder_path, "w") as log_file:
                for log_message in self.log_messages:
                    log_file.write(log_message + "\n")
        self.log_message(f"all log save to {folder_path}")



    def save_to_csv(self):
        # Get data from multiple charts (subplots) in the plt figure and save to a single CSV file
        fig = plt.gcf()  # Get the current figure
        data_to_save = []
        for ax in fig.get_axes():
            subplot_data = []
            for line in ax.get_lines():
                x_data = line.get_xdata()
                y_data = line.get_ydata()
                subplot_data.append(list(zip(x_data, y_data)))
            if subplot_data:
                data_to_save.append(subplot_data)
        # Save data to a CSV file
        if data_to_save:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            file_path, _ = QFileDialog.getSaveFileName(None, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)",
                                                       options=options)

            if file_path:
                # Save data to the CSV file
                with open(file_path, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    for subplot_data in data_to_save:
                        writer.writerow([])  # Add an empty row between subplots
                        for data in subplot_data:
                            writer.writerows(data)
        self.log_message("saved_plots")


    def destroy_plots(self):
        plt.close('all')
        self.log_message("destroy_plots")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

