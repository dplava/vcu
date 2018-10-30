import re


def main():

    col_file = input("Please enter the name of the input file, without the extension. The file must be in the input "
                     "folder. (e.g. for the input file input/collection.xml, enter 'collection') \n ---> ")

    output_name = input("Please enter the base file name for the output files. (e.g. rpr_20181030) \n ---> ")

    # for easier testing on the same file
    # col_file = 'newrpr103018'
    # output_name = 'rpr-20181030'

    input_filepath = 'input/' + col_file + '.xml'
    fp_out = None

    with open(input_filepath) as fp_in:
            line = fp_in.readline()
            count_records = 0
            provenance_additions = 0
            rights_substitutions = 0
            thumbnail_additions = 0
            url_substitutions = 0
            while line:

                # replace any special characters that don't decode (? in little diamond) with a space
                line = line.replace(u'\ufffd', ' ')

                # fix issue with apostrophes
                line = line.replace("&#x27;", "'")

                # replace &
                # line = line.replace("&amp;", "&")

                # changes dc to dcterms
                if line.startswith('<dc:'):
                    line = line.replace('<dc:', '<dcterms:', 1)
                    line = line.replace('</dc:', '</dcterms:')

                # replace Stillimage in type field
                if line.startswith('<dcterms:type>') and "Stillimage" in line:
                    line = line.replace("Stillimage", "Still Image")

                # replace xml alternative tag with title tag
                if line.startswith('<dcterms:alternative>'):
                    line = line.replace("<dcterms:alternative>", "<dcterms:title>")
                    line = line.replace("</dcterms:alternative>", "</dcterms:title>")

                # replace xml issued tag with created tag
                if line.startswith('<dcterms:issued>'):
                    line = line.replace("<dcterms:issued>", "<dcterms:created>")
                    line = line.replace("</dcterms:issued>", "</dcterms:created>")

                # add page to page number description
                if re.match('<dcterms:description>(\d+)</dcterms:description>', line):
                    page = re.search('<dcterms:description>(\d+)</dcterms:description>', line).group(1)
                    line = re.sub('\d+', 'p. ' + page, line)

                # indicates the start of a record
                if fp_out is None or fp_out.closed:
                    if '<metadata>' in line:
                        # create and open output file
                        output_file = 'output/' + output_name + '_' + str(count_records) + '.xml'
                        fp_out = open(output_file, 'w+')
                        count_records += 1

                        # write header information
                        fp_out.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                        fp_out.write('<?xml-model href="dplava.xsd" type="application/xml" schematypens='
                                     '"http://purl.oclc.org/dsdl/schematron"?>\n')
                        fp_out.write('<mdRecord xmlns="http://dplava.lib.virginia.edu" xmlns:xsi='
                                     '"http://www.w3.org/2001/XMLSchema-instance" xmlns:dc='
                                     '"http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                                     'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:edm='
                                     '"http://www.europeana.eu/schemas/edm/" xsi:schemaLocation='
                                     '"http://dplava.lib.virginia.edu/dplava.xsd">\n')
                else:
                    # indicates the end of a record
                    if '</metadata>' in line:
                        fp_out.write('</mdRecord>')
                        fp_out.close()

                    # this adds in provenance
                    elif line.startswith('<dcterms:source>'):
                        fp_out.write("<dcterms:provenance>Virginia Commonwealth University</dcterms:provenance>\n")
                        fp_out.write(line)
                        provenance_additions += 1

                    # this changes the rights statement
                    elif line.startswith('<dcterms:rights>'):
                        fp_out.write("<dcterms:rights>http://rightsstatements.org/vocab/NoC-US/1.0/</dcterms:rights>\n")
                        rights_substitutions += 1

                    # changes the URL and adds thumbnail URL
                    elif line.startswith('<dcterms:identifier>http://'):
                        if line.startswith('<dcterms:identifier>http://digital'):
                            if not line.endswith("</oai_qdc:qualifieddc>\n"):
                                print(line)
                                print("ERROR: unexpected input")

                            # get url and col_id string
                            url = re.sub('<[^>]+>', '', line).strip()
                            url = url.replace("http://", "https://", 1)
                            if not url.split('/')[-2] == "id":
                                print('ERROR: URL parse problem')
                            col_id = url.split('/')[-3] + '/' + url.split('/')[-2] + '/' + url.split('/')[-1]

                            # write url line
                            fp_out.write("<edm:isShownAt>" + url + "</edm:isShownAt>\n")
                            url_substitutions += 1

                            # write thumbnail line
                            thumb = 'https://digital.library.vcu.edu/utils/getthumbnail/collection/' + col_id
                            fp_out.write("<edm:preview>" + thumb + "</edm:preview>\n")
                            thumbnail_additions += 1

                    # change jpeg type field to medium field
                    elif line.startswith('<dcterms:type>') and "image/jp2" in line:
                        line = line.replace("type", "medium")
                        fp_out.write(line)

                    # expand type, medium field
                    elif ";" in line and (line.startswith('<dcterms:type>')
                                          or line.startswith('<dcterms:medium')
                                          or line.startswith('<dcterms:subject')):

                        # swap out and then swap in special chars. ONLY WORKS IF ONLY ONE SPECIAL CHAR
                        special_char = ''
                        if '&amp;' in line:
                            special_char = re.search('(&\S*;)', line).group(1)
                            line = re.sub('&(\S*);', '#$%^', line)

                        tag = re.search('<dcterms:(\w*)>', line).group(1)
                        values = re.split(';', re.sub('<[^>]+>', '', line).strip())
                        for value in values:
                            # swap back in the special char
                            if '#$%^' in value:
                                value = value.replace('#$%^', special_char)
                            fp_out.write("<dcterms:" + tag + ">" + value.strip() + "</dcterms:" + tag + ">\n")

                    # regular line
                    elif line.startswith('<dcterms:'):
                        fp_out.write(line)

                line = fp_in.readline()

    print("Records: \t{}".format(count_records))
    print("Provenances: \t{}".format(provenance_additions))
    print("Rights: \t{}".format(rights_substitutions))
    print("Thumbnails: \t{}".format(thumbnail_additions))
    print("URLs: \t{}".format(url_substitutions))


if __name__ == "__main__":
        main()
