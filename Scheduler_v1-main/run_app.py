import os
import sys
import streamlit.web.cli as stcli

def main():
    # If bundled by PyInstaller, sys._MEIPASS holds the temp extraction directory
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    app_path = os.path.join(base_path, "Streamlit", "App.py")
    
    # Simulate the `streamlit run App.py` command
    sys.argv = ["streamlit", "run", app_path, "--global.developmentMode=false"]
    
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
