#!/usr/bin/env python
import sys
import asyncio
from functools import partial
from kasa import Discover
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout
)
from qasync import QEventLoop, asyncSlot


class QasaPlugQt(QWidget):
    def __init__(self):
        super().__init__()
        self.plugs = {}
        self.ui_elements = {}  # Stores references to avoid rebuilding widgets

        self.setup_window()

        # Start the initial discovery
        asyncio.ensure_future(self.discover_loop())

    def setup_window(self):
        self.setWindowTitle("QasaPlug (Qt6)")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        self.show()

    async def discover_loop(self):
        """Runs discovery periodically without blocking the UI."""
        while True:
            try:
                # Async discovery that doesn't freeze the GUI
                found_devices = await Discover.discover()

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

            except Exception as e:
                print(f"Discovery error: {e}")

            # Non-blocking sleep for 60 seconds
            await asyncio.sleep(60)

    def add_device_widget(self, addr, dev):
        """Creates the UI row for a new device."""
        if not dev.is_plug:
            return

        # Create Container
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_widget.setLayout(row_layout)

        # Name Label
        name_label = QLabel(dev.alias)

        # Power Label (for HS110)
        power_text = ""
        if dev.model.startswith("HS110") and dev.emeter_realtime:
            power_text = f"{dev.emeter_realtime.get('power', 0)} W"
        power_label = QLabel(power_text)

        # Toggle Button
        btn = QPushButton()
        btn.setCheckable(True)
        # Bind the specific address to this button's click event
        btn.clicked.connect(partial(self.handle_toggle, addr))

        # Add to layout
        row_layout.addWidget(name_label)
        row_layout.addWidget(power_label)
        row_layout.addWidget(btn)

        self.main_layout.addWidget(row_widget)

        # Store references so we can update them later without rebuilding
        self.ui_elements[addr] = {
            'widget': row_widget,
            'name_lbl': name_label,
            'power_lbl': power_label,
            'btn': btn
        }

        # Set initial state
        self.update_device_widget_state(addr, dev)

    def update_device_widget(self, addr, dev):
        """Updates the UI for an existing device."""
        if addr in self.ui_elements:
            self.update_device_widget_state(addr, dev)

    def update_device_widget_state(self, addr, dev):
        """Sets text and checked state based on device object."""
        elements = self.ui_elements[addr]

        # Update Name
        elements['name_lbl'].setText(dev.alias)

        # Update Power (if applicable)
        if dev.model.startswith("HS110") and dev.emeter_realtime:
            power_val = dev.emeter_realtime.get('power', 0)
            elements['power_lbl'].setText(f"{power_val:.1f} W")

        # Update Button State
        btn = elements['btn']

        # Temporarily block signals to prevent triggering 'handle_toggle' during update
        btn.blockSignals(True)
        if dev.is_on:
            btn.setText("Switch Off")
            btn.setChecked(True)
        else:
            btn.setText("Switch On")
            btn.setChecked(False)
        btn.blockSignals(False)

    @asyncSlot()
    async def handle_toggle(self, addr):
        """Handle button press asynchronously."""
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
            print(f"Error switching device: {e}")
            # Revert button state on failure
            btn.setChecked(not target_state)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # QEventLoop from qasync allows asyncio to run inside PyQt6
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = QasaPlugQt()

    with loop:
        loop.run_forever()
