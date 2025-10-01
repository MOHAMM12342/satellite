class AuthRouter:
    route_app_labels = {
        'auth',
        'admin',
        'contenttypes',
        'sessions',
        'authtoken',
        'authentification',
        'otp_totp',
        'two_factor',
        'otp_static'
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'auth_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'auth_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in self.route_app_labels:
            return db == 'auth_db'
        return db == 'default'

class IPrestrictRouter:
    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'iprestrict':
            return 'auth_db'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'iprestrict':
            return 'auth_db'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'iprestrict':
            return db == 'auth_db'
        return None
