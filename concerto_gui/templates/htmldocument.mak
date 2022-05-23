<!DOCTYPE html>

<html xmlns="http://www.w3.org/1999/xhtml" lang="${document.lang}">
    <head>
        <title>${ env.config.interface.get("browser_title", "Concerto") }</title>
        <base href="${document.base_url}" />
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <link rel="icon" type="image/png" sizes="32x32" href="${env.config.interface.get('favicon', 'concerto_gui/images/favicon.png')}" />

        ## EventSource polyfill for IE/Edge
        <script src="concerto_gui/js/EventSource.js" type="text/javascript"></script>

        % for resource in document.head_content:
                ${resource}
        % endfor

        <%block name="head_extra_content"></%block>

        <script src="concerto_gui/js/LAB.min.js" type="text/javascript"></script>
        <script type="text/javascript">
            window.concerto_gui_config = { base_url: "${document.base_url}" };

            $.ajaxSetup({ url: "?" });
            $LAB.setGlobalDefaults({ BasePath: concerto_gui_config.base_url });
        </script>
    </head>
    <body>
     % for resource in document.body_content:
       ${resource}
     % endfor

     ${next.body()}
    </body>
</html>
