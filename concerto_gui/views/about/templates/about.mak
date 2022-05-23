<%!
from concerto_gui import version
%>

<div class="container">
  <div class="widget" role="dialog" aria-labelledby="dialogLabel" aria-hidden="true" data-widget-options="modal-lg">
    <link rel="stylesheet" type="text/css" href="about/css/about.css" />

    <div class="modal-header">
      <button type="button" class="close" data-dismiss="modal">&times;</button>
      <h5 class="modal-title">${ _("Concerto SIEM version %s") % version.__version__ }</h5>
    </div>

    <div class="modal-body about">
      <h5>${ _("Concerto SIEM is a \"Security Information and Event Management\" system") }</h5>
      <div class="software">
        <div class="col-sm-3">
          <img src="about/images/concerto-logo-400.png"/>
        </div>
        <p class="col-sm-9">
          ${ _("{concerto} is a security management solution that collects, filters, normalizes, correlates, stores and archives data from various sources of your information system. Based on all this information Concerto SIEM can provide a global vision of your system's security level and thus prevent attacks, intrusions as well as viral infections.").format(concerto="<a href='https://concerto-siem.github.io'>Concerto SIEM</a>") | n }
        </p>
      </div>
      <br/>
      <p>
        ${ _("Concerto SIEM are being developed by the %s company, designer, integrator and operator of mission critical systems.") % ("<a href='https://concerto-siem.github.io'>Concerto</a>") | n}
      </p>

      <div class="about_contact" class="panel">
        <div>
           <b>${ _("Contact") }</b>
           <p><a href="mailto:concerto-siem@gmail.com">concerto-siem@gmail.com</a></p>
        </div>
        <div>
           <b>${ _("Corporate") }</b>
           <p><a href="https://concerto-siem.github.io">concerto-siem.github.io</a></p>
        </div>
        <div>
           <b>${ _("Community") }</b>
           <p><a href="https://github.com/Concerto-SIEM">github.com/Concerto-SIEM</a></p>
        </div>

        <p class="copyright">Copyright &copy; 2022 Concerto. All rights reserved.</p>
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn btn-default widget-only" aria-hidden="true" data-dismiss="modal">${ _('Close') }</button>
    </div>
  </div>
</div>
