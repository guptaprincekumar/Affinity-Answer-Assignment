#!/usr/bin/env bash
# Print company name, headquarters location and founding year for every
# company in the S&P 500 constituents CSV, sorted by founding year.
#
# Usage: ./company_info.sh <csv-url>
#
# Output is tab-separated: NAME <TAB> LOCATION <TAB> FOUNDING_YEAR
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 <csv-url>" >&2
    exit 1
fi

url=$1

# CSV fields (see header row): 2 = Security (company name),
# 5 = Headquarters Location, 8 = Founded. Fields can contain quoted
# commas ("Saint Paul, Minnesota"), so the line is parsed with a small
# CSV-aware function instead of a plain comma split.
curl -sSfL "$url" | awk '
    NR == 1 { next }                       # skip the header row
    {
        sub(/\r$/, "")                     # tolerate CRLF line endings
        delete fields                      # do not carry values across ragged rows
        parse_csv_line($0, fields)
        # The Founded column can be "2013 (1888)" or "2020 (1915, ...)";
        # the first 4-digit number is the founding year of the listed entity.
        year = ""
        if (match(fields[8], /[0-9][0-9][0-9][0-9]/)) {
            year = substr(fields[8], RSTART, 4)
        }
        printf "%s\t%s\t%s\n", fields[2], fields[5], year
    }

    # Split a CSV line into fields[], honouring quotes: commas inside
    # quoted fields are kept, doubled quotes ("") become a literal quote.
    function parse_csv_line(line, fields,    i, n, ch, value, in_quotes) {
        n = 0
        value = ""
        in_quotes = 0
        for (i = 1; i <= length(line); i++) {
            ch = substr(line, i, 1)
            if (ch == "\"") {
                if (in_quotes && substr(line, i + 1, 1) == "\"") {
                    value = value "\""
                    i++
                } else {
                    in_quotes = !in_quotes
                }
            } else if (ch == "," && !in_quotes) {
                fields[++n] = value
                value = ""
            } else {
                value = value ch
            }
        }
        fields[++n] = value
        return n
    }
' | sort -t $'\t' -k3,3n
