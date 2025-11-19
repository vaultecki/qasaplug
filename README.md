# QasaPlug - TP-Link Kasa Smart Plug Controller

A modern PyQt6-based GUI application for controlling TP-Link Kasa smart plugs on your local network. Features real-time power monitoring, automatic device discovery, and a responsive async interface.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)

## Features

- 🔌 **Automatic Device Discovery** - Finds all TP-Link Kasa smart plugs on your network
- ⚡ **Real-time Power Monitoring** - Displays current power consumption for HS110 models
- 🎨 **Visual Status Indicators** - Color-coded buttons and LED indicators show device state
- 🔄 **Auto-refresh** - Devices update every 60 seconds automatically
- 🖱️ **Manual Refresh** - Quick refresh button for immediate updates
- 🌐 **Offline Detection** - Identifies and marks offline devices
- ⚠️ **Error Handling** - User-friendly error messages and robust error recovery
- 🚀 **Async Architecture** - Non-blocking UI powered by asyncio and qasync

## Screenshots

The interface shows:
- Device name and IP address
- Current power consumption (for HS110 models)
- Color-coded status indicators (green = on, gray = off, red = offline)
- Toggle buttons with visual feedback

## Requirements

- Python 3.8 or higher
- TP-Link Kasa smart plugs (HS100, HS110, or compatible models)
- Local network access to smart plugs

## Installation

1. **Clone or download this repository**

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install python-kasa PyQt6 qasync
```

3. **Run the application:**
```bash
python qasaplugqt.py
```

## Usage

### First Launch
1. Start the application
2. It will automatically discover all TP-Link Kasa smart plugs on your network
3. Devices appear in the list with their current status

### Controlling Devices
- **Turn On/Off**: Click the toggle button next to each device
- **Manual Refresh**: Click "Refresh Now" to immediately scan for devices
- **Power Monitoring**: HS110 models display real-time power consumption in watts

### Status Indicators
- 🟢 **Green dot** - Device is online and ON
- ⚫ **Gray dot** - Device is online and OFF
- 🔴 **Red dot** - Device is offline or unreachable

## Configuration

Edit the `Settings` class in `qasaplugqt.py` to customize behavior:

```python
class Settings:
    DISCOVERY_INTERVAL = 60  # Seconds between automatic scans
    SHOW_IP_ADDRESS = True   # Display IP addresses in the UI
    AUTO_RECONNECT = True    # Attempt to reconnect to offline devices
    ENABLE_POWER_MONITORING = True  # Show power consumption
```

## Supported Devices

This application works with TP-Link Kasa smart plugs including:
- HS100 - Smart Plug
- HS110 - Smart Plug with Energy Monitoring
- KP115 - Smart Plug Mini with Energy Monitoring
- And other compatible Kasa devices

## Architecture

The application uses:
- **PyQt6** for the graphical interface
- **python-kasa** for device communication
- **qasync** to integrate asyncio with PyQt6's event loop
- **asyncio** for non-blocking device operations

Key design features:
- Async/await patterns prevent UI freezing
- Widget recycling for efficient updates
- Optimistic UI updates for better responsiveness
- Proper error handling with user feedback

## Troubleshooting

**No devices found?**
- Ensure devices are on the same network
- Check firewall settings (UDP ports 9999 required)
- Verify devices are set up in the Kasa app first

**Devices show as offline?**
- Check network connectivity
- Restart the device
- Try manual refresh

**Toggle button doesn't work?**
- Check error messages in the console
- Verify device is reachable on the network
- Ensure no other apps are controlling the device

## Dependencies

- **python-kasa** - TP-Link Kasa smart home library
- **PyQt6** - Python bindings for Qt6
- **qasync** - Asyncio integration for Qt

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Built with [python-kasa](https://github.com/python-kasa/python-kasa)
- Uses [qasync](https://github.com/CabbageDevelopment/qasync) for async Qt integration

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review python-kasa documentation
3. Open an issue on GitHub

---

**Note**: This application requires local network access to your smart plugs. No cloud connection is required.