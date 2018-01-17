odoo.define('github_project.custom_fields', function (require) {
   var basic_fields = require('web.basic_fields');

   basic_fields.UrlWidget.include({
       _render: function () {
           this._super();
           var self = this;
           if(this.attrs.target === 'popup'){
                this.$el.on('click', function (ev) {
                    ev.preventDefault();
                    window.open(self.value, 'login', 'width=600, height=800, top=0, left=' + (screen.width - 600)/2);
                });
           }
       },
       _renderReadonly: function () {
           this._super();
           this.$el.attr('target', this.attrs.target ||'_blank');
       }
   });
});