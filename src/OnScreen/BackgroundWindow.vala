using Gtk;
using Gdk;
using Gst;
using GLib;
using WebKit;

using Komorebi.Utilities;

namespace Komorebi.OnScreen {

	// Global - Name of active wallpaper
	string wallpaperName;

	public class BackgroundWindow : Gtk.Window {

		// this webview acts as a wallpaper (if necessary)
		WebView webView = new WebView();
		GtkClutter.Actor webViewActor;

		GtkClutter.Embed embed;

		// Main container
		public Clutter.Actor mainActor { get; private set; }

		// Video Wallpaper
		ClutterGst.Playback videoPlayback;
		ClutterGst.Content videoContent;

		// Wallpaper pixbuf & image
		Clutter.Actor wallpaperActor = new Clutter.Actor();
		Pixbuf wallpaperPixbuf;
		Clutter.Image wallpaperImage = new Clutter.Image();

		// Date and time box itself
		DateTimeBox dateTimeBox;

		// Asset Actor
		AssetActor assetActor;

		// Current animation mode
		bool dateTimeBoxParallax = false;

		public BackgroundWindow (int monitorIndex) {

			title = "Desktop";

			// Get current monitor size
			getMonitorSize(monitorIndex);

			embed = new GtkClutter.Embed() {width_request = screenWidth, height_request = screenHeight};
			mainActor = embed.get_stage();
			desktopPath = Environment.get_user_special_dir(UserDirectory.DESKTOP);
			assetActor = new AssetActor(this);
			if (dateTimeVisible) {
				dateTimeBox = new DateTimeBox(this);
			}
			else {
				// Release the memory
				dateTimeBox = null;
			}
			if (wallpaperType == "web_page") {
				webViewActor = new GtkClutter.Actor.with_contents(webView);
			}
			else {
				// Release the memory
				webViewActor = null;
			}

			videoPlayback = new ClutterGst.Playback ();
			videoContent = new ClutterGst.Content ();
			// Fast seeks (key frame boundaries, default)
			videoPlayback.set_seek_flags (ClutterGst.SeekFlags.NONE);
			videoContent.player = videoPlayback;
			videoPlayback.set_audio_volume(0.0);

			// Setup widgets
			set_size_request(screenWidth, screenHeight);
			resizable = false;
			set_type_hint(WindowTypeHint.DESKTOP);
			set_keep_below(true);
			app_paintable = false;
			skip_pager_hint = true;
			skip_taskbar_hint = true;
			accept_focus = true;
			stick ();
			decorated = false;

			mainActor.background_color = Clutter.Color.from_string("black");

			wallpaperActor.set_size(screenWidth, screenHeight);
			assetActor.set_size(screenWidth, screenHeight);
			wallpaperActor.set_pivot_point (0.5f, 0.5f);

			// Add widgets
			mainActor.add_child(wallpaperActor);
			if (dateTimeVisible) {
				mainActor.add_child(dateTimeBox);
			}
			else if (wallpaperType == "web_page") {
			webViewActor.set_size(screenWidth, screenHeight);
				mainActor.add_child(webViewActor);
			}
			mainActor.add_child(assetActor);

			// add the widgets
			add(embed);

			// Don't get duration constant until the video is started (in initializeConfigFile())
			initializeConfigFile(); 
			if (wallpaperType == "video") {

				// [UPDATE] Switch to listening for eos signal (end of stream)
				videoPlayback.eos.connect(() => {
					// This code block will be executed when the "eos" signal is emitted
					// Set the playback progress to the beginning and restart playback
					videoPlayback.set_progress(0.0);
					videoPlayback.set_playing(true);
				});

				// [UPDATE] Connect a callback function to the "error" signal
				videoPlayback.error.connect((error) => {
					// This code block will be executed when the "error" signal is emitted
					stdout.printf("\nError occurred:\n");
					// Flush and recreate the Playback object
					videoPlayback = null;
					videoPlayback = new ClutterGst.Playback();
					var videoPath = @"file:///System/Resources/Komorebi/$wallpaperName/$videoFileName";
					videoPlayback.uri = videoPath;
					videoPlayback.set_audio_volume(0.0);
					videoPlayback.set_playing(true);
					videoContent.player = videoPlayback;

					// Prettify and log the properties of the Error object
					stdout.printf("Message: %s\n", error.message);
					stdout.printf("Domain: %" + uint32.FORMAT + "\n", error.domain);
					stdout.printf("Code: %d\n", error.code);
				});
			}
		}

		void getMonitorSize(int monitorIndex) {

			Rectangle rectangle;

			// Deprecated
			var screen = Gdk.Screen.get_default ();
			screen.get_monitor_geometry (monitorIndex, out rectangle);

			screenHeight = rectangle.height;
			screenWidth = rectangle.width;

			move(rectangle.x, rectangle.y);

		}

		public void initializeConfigFile () {

			setWallpaper();

			if(dateTimeVisible) {
			
				if(dateTimeAlwaysOnTop)
					mainActor.set_child_above_sibling(dateTimeBox, assetActor);
				else
					mainActor.set_child_below_sibling(dateTimeBox, assetActor);
				
				dateTimeBox.setDateTime();

			} 

			if((wallpaperType != "video" && wallpaperType != "web_page") && assetVisible)
				assetActor.setAsset();
			else
				assetActor.shouldAnimate();
		}

		void setWallpaper() {

			var scaleWidth = screenWidth;
			var scaleHeight = screenHeight;

			if(wallpaperParallax) {

				wallpaperActor.scale_y = 1.05f;
				wallpaperActor.scale_x = 1.05f;

			} else {

				wallpaperActor.scale_y = 1.00f;
				wallpaperActor.scale_x = 1.00f;   
			}

				
				if(wallpaperType == "video") {

					var videoPath = @"file:///System/Resources/Komorebi/$wallpaperName/$videoFileName";
					videoPlayback.uri = videoPath;
					videoPlayback.playing = true;

					wallpaperActor.set_content(videoContent);

					return;
				
				} else {
				
					videoPlayback.playing = false;
					videoPlayback.uri = "";
				}

			if (wallpaperType == "web_page") {

				wallpaperFromUrl(webPageUrl);

				wallpaperActor.set_content(null);
				wallpaperPixbuf = null;

				if(webViewActor.get_parent() != wallpaperActor)
					wallpaperActor.add_child(webViewActor);

				return;

			} else {

				// remove webViewActor
				if(webViewActor.get_parent() == wallpaperActor)
					wallpaperActor.remove_child(webViewActor);
			}

			wallpaperActor.set_content(wallpaperImage);

			wallpaperPixbuf = new Gdk.Pixbuf.from_file_at_scale(@"/System/Resources/Komorebi/$wallpaperName/wallpaper.jpg",
																scaleWidth, scaleHeight, false);

			wallpaperImage.set_data (wallpaperPixbuf.get_pixels(), Cogl.PixelFormat.RGB_888,
							 wallpaperPixbuf.get_width(), wallpaperPixbuf.get_height(),
							 wallpaperPixbuf.get_rowstride());
		}

		// loads a web page from a URL
		public void wallpaperFromUrl(owned string url) {

			url = url.replace("{{screen_width}}", @"$screenWidth").replace("{{screen_height}}", @"$screenHeight");

			webView.load_uri(url);
		}

		/* Shows the window */
		public void fadeIn() {
			show_all();
			if (dateTimeVisible) {
				dateTimeBox.fadeIn();
			}
		}

		public bool contains_point(int x, int y) {
			int wl, wt, wr, wb;
			get_position(out wl, out wt);
			get_size(out wr, out wb);
			wr += wl;
			wb += wt;

			return (x >= wl && y >= wt && x < wr && y < wb);
		}
	}
}
