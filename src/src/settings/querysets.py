from django.db.models import QuerySet


class DepartmentQuerySet(QuerySet):

    def only_enableds(self):
        """
        Retorna solo los departamentos
        que esten marcados como activos
        """

        return self.filter(is_actived=True)