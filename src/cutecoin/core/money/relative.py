from PyQt5.QtCore import QObject, QCoreApplication, QT_TRANSLATE_NOOP, QLocale


class Relative():
    _NAME_STR_ = QT_TRANSLATE_NOOP('Relative', 'UD')
    _REF_STR_ = QT_TRANSLATE_NOOP('Relative',  "{0} {1}UD {2}")
    _UNITS_STR_ = QT_TRANSLATE_NOOP('Relative',  "UD {0}")

    def __init__(self, amount, community, app):
        self.amount = amount
        self.community = community
        self.app = app

    @classmethod
    def translated_name(cls):
        return QCoreApplication.translate('Relative', Relative._NAME_STR_)

    @classmethod
    def units(self, currency):
        return QCoreApplication.translate("Relative", Relative._UNITS_STR_).format(currency)

    @classmethod
    def diff_units(self, currency):
        return self.units(currency)

    def value(self):
        """
        Return relaive value of amount
    type
        :param int amount:   Value
        :param cutecoin.core.community.Community community: Community instance
        :return: float
        """
        if self.community.dividend > 0:
            return self.amount / float(self.community.dividend)
        else:
            return 0

    def differential(self):
        return self.value()

    def _to_si(self, value):
        prefixes = ['', 'd', 'c', 'm', 'µ', 'n', 'p', 'f', 'a', 'z', 'y']
        scientific_value = value
        prefix_index = 0
        prefix = ""

        while int(scientific_value) == 0:
            if prefix_index > 3:
                scientific_value *= 1000
            else:
                scientific_value *= 10
            prefix_index += 1

        if prefix_index < len(prefixes):
            prefix = prefixes[prefix_index]
            localized_value = QLocale().toString(float(scientific_value), 'f', self.app.preferences['digits_after_comma'])
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        return localized_value, prefix

    def localized(self, units=False, international_system=False):
        value = self.value()
        prefix = ""
        if international_system:
            localized_value, prefix = self._to_si(value)
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("Relative", Relative._REF_STR_) \
                .format(localized_value,
                        prefix,
                        self.community.short_currency if units else "")
        else:
            return localized_value

    def diff_localized(self, units=False, international_system=False):
        value = self.differential()
        prefix = ""
        if international_system and value != 0:
            localized_value, prefix = self._to_si(value)
        else:
            localized_value = QLocale().toString(float(value), 'f', self.app.preferences['digits_after_comma'])

        if units or international_system:
            return QCoreApplication.translate("Relative", Relative._REF_STR_)\
                .format(localized_value,
                    prefix,
                    self.community.short_currency if units else "")
        else:
            return localized_value