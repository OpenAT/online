outdatedBrowserRework(
    {
        browserSupport: {
            'Chrome': 60, // Includes Chrome for mobile devices
            'Edge': false,
            'Safari': false,
            'Mobile Safari': false,
            'Firefox': false,
            'Opera': false,
            'Vivaldi': false,
            // You could specify minor version too for those browsers that need it.
            // 'Yandex': { major: 17, minor: 10 },
            // You could specify a version here if you still support IE in 2017.
            // You could also instead seriously consider what you're doing with your time and budget
            'IE': false
        },
        requireChromeOnAndroid: false,
        isUnknownBrowserOK: false,
        messages: {
            en: {
                outOfDate: "Your browser is not supported!",
                unsupported: "Your browser is not supported for e-mail template editing! Please use an up-to-date version of Google Chrome!",
                update: {
                    web: "Update your browser now!",
                    googlePlay: "Please install Chrome from Google Play",
                    appStore: "Please update iOS from the Settings App"
                },
                // You can set the URL to null if you do not want a clickable link or provide
                // your own markup in the `update.web` message.
                url: "https://www.google.de/chrome/",
                callToAction: "Please change your browser now!",
                close: "Close"
            },
            de: {
                outOfDate: "Ihr Browser ist nicht untertütz!",
                update: {
                    web: "Bitte verwenden Sie eine aktuelle Version von Google Chrome für das Editieren von E-Mail Vorlagen!",
                    googlePlay: "Please install Chrome from Google Play",
                    appStore: "Please update iOS from the Settings App"
                },
                url: "https://www.google.de/chrome/",
                callToAction: "Den Browser jetzt aktualisieren!",
                close: "Schließen"
            },
        }
    }
);
