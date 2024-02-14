using Komorebi.OnScreen;
using Komorebi.Utilities;

namespace Komorebi {

    BackgroundWindow[] backgroundWindows;
    public static int monitorCount;
    public static int targetMonitor;

public static void main (string [] args) {

    print("Welcome to Komorebi\n");

    if (args.length > 1) {
        targetMonitor = int.parse(args[1]);
        if (targetMonitor < 0) {
            print("[ERROR]: Invalid monitor number. Program will run on the first monitor.\n");
            targetMonitor = 0;
        }
    }


    GtkClutter.init (ref args);
    Gtk.init (ref args);

    readConfigurationFile(targetMonitor);

        Gst.init (ref args);

    Gtk.Settings.get_default().gtk_application_prefer_dark_theme = true;

    var screen = Gdk.Screen.get_default ();
    monitorCount = screen.get_n_monitors();

    if (targetMonitor >= monitorCount) {
        print("[ERROR]: Monitor number exceeds number of available monitors. Program will run on the first monitor.\n");
        // Set to last monitor
        targetMonitor = monitorCount - 1;
    }

    //  initializeClipboard(screen);
    readWallpaperFile();

    backgroundWindows = new BackgroundWindow[monitorCount];
    for (int i = 0; i < monitorCount; ++i) {
        if (i == targetMonitor) {
            backgroundWindows[i] = new BackgroundWindow(i);
        }
    }

    var mainSettings = Gtk.Settings.get_default ();
    // mainSettings.set("gtk-xft-dpi", (int) (1042 * 100), null);
    mainSettings.set("gtk-xft-antialias", 1, null);
    mainSettings.set("gtk-xft-rgba" , "none", null);
    mainSettings.set("gtk-xft-hintstyle" , "slight", null);

    for (int i = 0; i < monitorCount; ++i) {
        if (i == targetMonitor) {
            backgroundWindows[i].fadeIn();
        }
    }

    Clutter.main();
}
}
