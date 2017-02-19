

def _parse_row(r):
    marriage = _parse_date(r, 3)
    hbirth = _parse_date(r, 8)
    hdeath = _parse_date(r, 12)
    wbirth = _parse_date(r, 18)
    wdeath = _parse_date(r, 22)
    row = [
        r[0], r[1], r[2], marriage,
        r[6], r[7], hbirth, r[11], hdeath, r[15],
        r[16], r[17], hbirth, r[21], hdeath, r[25],
    ]
    return "\t".join([str(i) for i in row])


def _parse_date(r, index):
    return f"{r[index]}-{r[index+1]}-{r[index+2]}"


class Family:
    """
    """
    def __init__(self, row):
        self._row = row

    @staticmethod
    def row_header():
        return ",".join([
            "mrin", "husband_id", "wife_id", "marriage_date",
            "husband_name", "husband_surname", "husband_birth_date",
            "husband_birth_place", "husband_death_date", "husband_death_place",
            "wife_name", "wife_surname", "wife_birth_date", "wife_birth_place",
            "wife_death_date", "wife_death_place",
        ])

    def tsv(self):
        """Return the data as a tab seperated row
        """
        return _parse_row(self._row)

