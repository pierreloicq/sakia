"""
Created on 5 févr. 2014

@author: inso
"""

from ..tools.exceptions import NoPeerAvailable, MembershipNotFoundError
from PyQt5.QtCore import QAbstractTableModel, QSortFilterProxyModel, Qt, \
                        QDateTime, QModelIndex, QLocale, QEvent
from PyQt5.QtGui import QColor, QIcon
import logging
import asyncio


class IdentitiesFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
        super().setSourceModel(sourceModel)

    def change_community(self, community):
        self.community = community
        self.sourceModel().change_community(community)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)
        left_data = 0 if left_data is None else left_data
        right_data = 0 if right_data is None else right_data
        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        if source_index.isValid():
            source_data = self.sourceModel().data(source_index, role)
            expiration_col = self.sourceModel().columns_ids.index('expiration')
            expiration_index = self.sourceModel().index(source_index.row(), expiration_col)

            STATUS_NOT_MEMBER = 0
            STATUS_MEMBER = 1
            STATUS_EXPIRE_SOON = 3
            status = STATUS_NOT_MEMBER
            expiration_data = self.sourceModel().data(expiration_index, Qt.DisplayRole)
            current_time = QDateTime().currentDateTime().toMSecsSinceEpoch()
            sig_validity = self.sourceModel().sig_validity()
            warning_expiration_time = int(sig_validity / 3)
            #logging.debug("{0} > {1}".format(current_time, expiration_data))

            if expiration_data is not None:
                status = STATUS_MEMBER
                if current_time > (expiration_data*1000):
                    status = STATUS_NOT_MEMBER
                elif current_time > ((expiration_data*1000) - (warning_expiration_time*1000)):
                    status = STATUS_EXPIRE_SOON

            if role == Qt.DisplayRole:
                if source_index.column() in (self.sourceModel().columns_ids.index('renewed'),
                                             self.sourceModel().columns_ids.index('expiration')):
                    if source_data is not None:
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(source_data).date(),
                            QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                        )
                    else:
                        return ""
                if source_index.column() == self.sourceModel().columns_ids.index('publication'):
                    if source_data is not None:
                        return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(source_data),
                            QLocale.dateTimeFormat(QLocale(), QLocale.LongFormat)
                        )
                    else:
                        return ""
                if source_index.column() == self.sourceModel().columns_ids.index('pubkey'):
                    return "pub:{0}".format(source_data[:5])

            if role == Qt.ForegroundRole:
                if status == STATUS_EXPIRE_SOON:
                    return QColor("darkorange").darker(120)
                elif status == STATUS_NOT_MEMBER:
                    return QColor(Qt.red)
                else:
                    return QColor(Qt.blue)
            if role == Qt.DecorationRole and source_index.column() == self.sourceModel().columns_ids.index('uid'):
                if status == STATUS_NOT_MEMBER:
                    return QIcon(":/icons/not_member")
                elif status == STATUS_MEMBER:
                    return QIcon(":/icons/member")
                elif status == STATUS_EXPIRE_SOON:
                    return QIcon(":/icons/member_warning")

            return source_data


class IdentitiesTableModel(QAbstractTableModel):

    """
    A Qt abstract item model to display communities in a tree
    """

    def __init__(self, parent=None):
        """
        Constructor
        """
        super().__init__(parent)
        self.community = None
        self.columns_titles = {'uid': lambda: self.tr('UID'),
                               'pubkey': lambda: self.tr('Pubkey'),
                               'renewed': lambda: self.tr('Renewed'),
                               'expiration': lambda: self.tr('Expiration'),
                               'publication': lambda: self.tr('Publication'),
                               'validation': lambda: self.tr('Validation'),}
        self.columns_ids = ('uid', 'pubkey', 'renewed', 'expiration', 'publication')
        self.identities_data = []
        self._sig_validity = 0

    def change_community(self, community):
        self.community = community

    def sig_validity(self):
        return self._sig_validity

    @property
    def pubkeys(self):
        """
        Ge
    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)t pubkeys of displayed identities
        """
        return [i[1] for i in self.identities_data]

    async def identity_data(self, identity):
        """
        Return the identity in the form a tuple to display
        :param sakia.core.registry.Identity identity: The identity to get data from
        :return: The identity data in the form of a tuple
        :rtype: tuple
        """
        try:
            join_date = await identity.get_join_date(self.community)
            expiration_date = await identity.get_expiration_date(self.community)
        except MembershipNotFoundError:
            join_date = None
            expiration_date = None

        if identity.sigdate:
            sigdate_ts = await self.community.time(identity.sigdate.number)
        else:
            sigdate_ts = None

        return identity.uid, identity.pubkey, join_date, expiration_date, sigdate_ts

    async def refresh_identities(self, identities):
        """
        Change the identities to display

        :param sakia.core.registry.IdentitiesRegistry identities: The new identities to display
        """
        logging.debug("Refresh {0} identities".format(len(identities)))
        self.beginResetModel()
        self.identities_data = []
        self.endResetModel()
        self.beginResetModel()
        identities_data = []
        requests_coro = []
        for identity in identities:
            coro = asyncio.ensure_future(self.identity_data(identity))
            requests_coro.append(coro)

        identities_data = await asyncio.gather(*requests_coro)

        if len(identities) > 0:
            try:
                parameters = await self.community.parameters()
                self._sig_validity = parameters['sigValidity']
            except NoPeerAvailable as e:
                logging.debug(str(e))
                self._sig_validity = 0
        self.identities_data = identities_data
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.identities_data)

    def columnCount(self, parent):
        return len(self.columns_ids)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            col_id = self.columns_ids[section]
            return self.columns_titles[col_id]()

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            identity_data = self.identities_data[row]
            return identity_data[col]

    def identity_index(self, pubkey):
        try:
            row = self.pubkeys.index(pubkey)
            index_start = self.index(row, 0)
            index_end = self.index(row, len(self.columns_ids))
            return (index_start, index_end)
        except ValueError:
            return (QModelIndex(), QModelIndex())

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
