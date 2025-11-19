#!/usr/bin/env python
import sys
import asyncio
from functools import partial
from kasa import Discover
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from qasync import QEventLoop, asyncSlot


class Settings:
    """Application configuration"""
    DISCOVERY_INTERVAL = 60  # seconds
    SHOW_IP_ADDRESS = True
    AUTO_RECONNECT = True
    ENABLE_POWER_MONITORING = True


class QasaPlugQt(QWidget):
    def __init__(self):
        super().__init__()
        self.plugs = {}
        self.ui_elements = {}  # Stores references to avoid rebuilding widgets
        self.is_discovering = False

        self.setup_window()

        # Start the initial discovery
        asyncio.ensure_future(self.discover_loop())

    def setup_window(self):
        """Initialize the main window and UI layout"""
        self.setWindowTitle("QasaPlug - TP-Link Kasa Control")
        self.setMinimumWidth(500)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header_label = QLabel("Smart Plugs")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.clicked.connect(self.manual_refresh)

        self.status_label = QLabel("Discovering devices...")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")

        header_layout.addWidget(header_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(header_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Device list container
        self.device_layout = QVBoxLayout()
        main_layout.addLayout(self.device_layout)

        main_layout.addStretch()

        self.show()

    async def discover_loop(self):
        """Runs discovery periodically without blocking the UI"""
        while True:
            await self.discover_devices()
            await asyncio.sleep(Settings.DISCOVERY_INTERVAL)

    async def discover_devices(self):
        """Discover devices on the network"""
        if self.is_discovering:
            return

        self.is_discovering = True
        self.status_label.setText("Discovering...")
        self.refresh_btn.setEnabled(False)

        try:
            # Async discovery that doesn't freeze the GUI
            found_devices = await Discover.discover()

            # Track which devices are currently online
            current_ips = set(found_devices.keys())
            previous_ips = set(self.plugs.keys())

            # Mark offline devices
            offline_ips = previous_ips - current_ips
            for addr in offline_ips:
                self.mark_device_offline(addr)

            # Sort devices by IP for consistent display order
            sorted_ips = sorted(found_devices.keys())

            for addr in sorted_ips:
                dev = found_devices[addr]

                # If we haven't seen this plug, or we need to update it
                if addr not in self.plugs:
                    # Initialize connection
                    await dev.update()
                    self.plugs[addr] = dev
                    self.add_device_widget(addr, dev)
                else:
                    # Update existing plug state
                    self.plugs[addr] = dev
                    await dev.update()
                    self.update_device_widget(addr, dev)

            device_count = len([d for d in self.plugs.values() if hasattr(d, 'is_plug') and d.is_plug])
            self.status_label.setText(f"Found {device_count} device(s)")

        except Exception as e:
            print(f"Discovery error: {e}")
            self.show_error(f"Discovery failed: {str(e)}")
            self.status_label.setText("Discovery failed")

        finally:
            self.is_discovering = False
            self.refresh_btn.setEnabled(True)

    @asyncSlot()
    async def manual_refresh(self):
        """Manually trigger device discovery"""
        await self.discover_devices()

    def add_device_widget(self, addr, dev):
        """Creates the UI row for a new device"""
        if not dev.is_plug:
            return

        # Create Container
        row_widget = QWidget()
        row_widget.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 5px;
                margin: 2px;
            }
        """)
        row_layout = QHBoxLayout()
        row_widget.setLayout(row_layout)

        # Status indicator (LED-style)
        status_indicator = QLabel("●")
        status_indicator.setStyleSheet("font-size: 20px; color: #999;")
        status_indicator.setFixedWidth(20)

        # Device info container
        info_layout = QVBoxLayout()

        # Name Label
        name_label = QLabel(dev.alias)
        name_label.setStyleSheet("font-weight: bold; font-size: 13px;")

        # IP Address Label
        ip_label = QLabel(f"IP: {addr}" if Settings.SHOW_IP_ADDRESS else "")
        ip_label.setStyleSheet("color: #666; font-size: 10px;")

        info_layout.addWidget(name_label)
        if Settings.SHOW_IP_ADDRESS:
            info_layout.addWidget(ip_label)

        # Power Label (for HS110)
        power_label = QLabel("")
        power_label.setStyleSheet("font-size: 12px; color: #333;")
        power_label.setMinimumWidth(80)
        power_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Toggle Button
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setMinimumWidth(100)
        # Bind the specific address to this button's click event
        btn.clicked.connect(partial(self.handle_toggle, addr))

        # Add to layout
        row_layout.addWidget(status_indicator)
        row_layout.addLayout(info_layout)
        row_layout.addStretch()
        row_layout.addWidget(power_label)
        row_layout.addWidget(btn)

        self.device_layout.addWidget(row_widget)

        # Store references so we can update them later without rebuilding
        self.ui_elements[addr] = {
            'widget': row_widget,
            'name_lbl': name_label,
            'ip_lbl': ip_label,
            'power_lbl': power_label,
            'btn': btn,
            'status_indicator': status_indicator,
            'is_online': True
        }

        # Set initial state
        self.update_device_widget_state(addr, dev)

    def update_device_widget(self, addr, dev):
        """Updates the UI for an existing device"""
        if addr in self.ui_elements:
            # Mark device as online again if it was offline
            if not self.ui_elements[addr]['is_online']:
                self.ui_elements[addr]['is_online'] = True
                self.ui_elements[addr]['widget'].setEnabled(True)
                self.ui_elements[addr]['widget'].setStyleSheet("""
                    QWidget {
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        padding: 5px;
                        margin: 2px;
                    }
                """)

            self.update_device_widget_state(addr, dev)

    def mark_device_offline(self, addr):
        """Mark a device as offline"""
        if addr in self.ui_elements:
            elements = self.ui_elements[addr]
            elements['is_online'] = False
            elements['widget'].setEnabled(False)
            elements['widget'].setStyleSheet("""
                QWidget {
                    background-color: #e9ecef;
                    border-radius: 5px;
                    padding: 5px;
                    margin: 2px;
                    opacity: 0.6;
                }
            """)
            elements['status_indicator'].setStyleSheet("font-size: 20px; color: #dc3545;")
            elements['power_lbl'].setText("Offline")

    def update_device_widget_state(self, addr, dev):
        """Sets text and checked state based on device object"""
        elements = self.ui_elements[addr]

        # Update Name
        elements['name_lbl'].setText(dev.alias)

        # Update Power (if applicable and enabled)
        if Settings.ENABLE_POWER_MONITORING and dev.model.startswith("HS110") and dev.emeter_realtime:
            power_val = dev.emeter_realtime.get('power', 0)
            elements['power_lbl'].setText(f"{power_val:.1f} W")
        else:
            elements['power_lbl'].setText("")

        # Update Button State and styling
        btn = elements['btn']

        # Temporarily block signals to prevent triggering 'handle_toggle' during update
        btn.blockSignals(True)
        if dev.is_on:
            btn.setText("Turn Off")
            btn.setChecked(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #90EE90;
                    border: 1px solid #7CCD7C;
                    border-radius: 3px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7CCD7C;
                }
            """)
            # Green indicator for ON
            elements['status_indicator'].setStyleSheet("font-size: 20px; color: #28a745;")
        else:
            btn.setText("Turn On")
            btn.setChecked(False)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #FFB6C1;
                    border: 1px solid #FF9FAF;
                    border-radius: 3px;
                    padding: 5px 15px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #FF9FAF;
                }
            """)
            # Gray indicator for OFF
            elements['status_indicator'].setStyleSheet("font-size: 20px; color: #6c757d;")
        btn.blockSignals(False)

    @asyncSlot()
    async def handle_toggle(self, addr):
        """Handle button press asynchronously"""
        dev = self.plugs.get(addr)
        if not dev:
            return

        btn = self.ui_elements[addr]['btn']
        # Optimistic UI update: assume it worked, revert if it fails
        target_state = btn.isChecked()

        try:
            if target_state:
                await dev.turn_on()
            else:
                await dev.turn_off()

            await dev.update()
            self.update_device_widget_state(addr, dev)

        except Exception as e:
            error_msg = f"Error switching device: {str(e)}"
            print(error_msg)
            self.show_error(error_msg)
            # Revert button state on failure
            btn.blockSignals(True)
            btn.setChecked(not target_state)
            btn.blockSignals(False)

    def show_error(self, message):
        """Display error message to user"""
        QMessageBox.warning(self, "Error", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # QEventLoop from qasync allows asyncio to run inside PyQt6
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = QasaPlugQt()

    with loop:
        loop.run_forever()
