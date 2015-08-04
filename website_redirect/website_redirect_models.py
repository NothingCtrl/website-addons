from openerp import api, models, fields, SUPERUSER_ID
from openerp.http import request
import fnmatch
import werkzeug.utils
from werkzeug.exceptions import NotFound

class website_redirect(models.Model):
    _name = 'website.redirect'

    _order = 'sequence,id'

    name = fields.Char('Name')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence')
    domain = fields.Char('Domain Name', placeholder='odoo.com', help='keep empty to apply rules for any domain')

    rule_ids = fields.One2many('website.redirect.rule', 'redirect_id', string='Rules')

class website_redirect(models.Model):
    _name = 'website.redirect.rule'

    _order = 'sequence,id'
    sequence = fields.Integer('Sequence')
    pattern = fields.Char('From', help='Unix shell-style wildcards. Check https://docs.python.org/2/library/fnmatch.html for details', required=True)
    target = fields.Char('To', required=True)
    redirect_id = fields.Many2one('website.redirect')

class ir_http(models.AbstractModel):
    _inherit = 'ir.http'

    def _handle_exception(self, exception, code=500):
        if code == 404 or isinstance(exception, NotFound):
            redirect = self.try_redirect()
            if redirect:
                return redirect
        return super(ir_http, self)._handle_exception(exception, code=code)

    def try_redirect(self):
        host = request.httprequest.environ.get('HTTP_HOST', '').split(':')[0]
        www, _, h = host.partition('.')
        if www == 'www':
            host = h
        path = request.httprequest.path
        print 'try_redirect', host, path
        for redirect in request.env['website.redirect'].sudo().search(['|', ('domain', '=', False), ('domain', '=', host)]):
            for rule in redirect.rule_ids:
                if fnmatch.fnmatch(path, rule.pattern):
                    code = 302
                    return werkzeug.utils.redirect(rule.target, code)
        return None