import re


def main():

    col_file = input("Please enter the name of the input file, without the extension. The file must be in the input "
                     "folder. (e.g. for the input file input/collection.xml, enter 'collection') \n ---> ")

    collection_name = input("Please enter the name of the collection as you would like it to display. \n ---> ")

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

                # fix issue with apostrophes
                if "&#x27;" in line:
                    line = line.replace("&#x27;", "'")

                # changes dc to dcterms
                if line.startswith('<dc:'):
                    line = line.replace('<dc:', '<dcterms:', 1)
                    line = line.replace('</dc:', '</dcterms:')

                # indicates the start of a record
                if fp_out is None or fp_out.closed:
                    if '<metadata>' in line:
                        # create and open output file
                        output_file = 'output/' + col_file + '_transformed_' + str(count_records) + '.xml'
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
                        fp_out.write("<dcterms:rights>http://rightsstatements.org/vocab/InC/1.0/</dcterms:rights>\n")
                        rights_substitutions += 1

                    # changes the URL and adds thumbnail URL
                    elif line.startswith('<dcterms:identifier>http://'):
                        if line.startswith('<dcterms:identifier>http://digital'):
                            if not line.endswith("</oai_qdc:qualifieddc>\n"):
                                print(line)
                                print("ERROR: unexpected input")

                            # get url and col_id string
                            url = re.split('[<>]', line)[2]
                            url = url.replace("http://", "https://", 1)
                            col_id = url.split('/')[6] + '/' + url.split('/')[7] + '/' + url.split('/')[8]

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

                    # expand type field
                    elif line.startswith('<dcterms:type>') and ";" in line:
                        if "Stillimage" in line:
                            line = line.replace("Stillimage", "Still Image")

                        values = re.split(';', re.sub('<[^>]+>', '', line).strip())
                        for value in values:
                            fp_out.write("<dcterms:type>" + value.strip() + "</dcterms:type>\n")

                    # expand type field
                    elif line.startswith('<dcterms:medium>') and ";" in line:

                        values = re.split(';', re.sub('<[^>]+>', '', line).strip())
                        for value in values:
                            fp_out.write("<dcterms:medium>" + value.strip() + "</dcterms:medium>\n")

                    # fix little box in isPartOf (not sure why this started showing up!!!
                    elif line.startswith('<dcterms:isPartOf>'):
                        fp_out.write(
                            '<dcterms:isPartOf>' + collection_name + '</dcterms:isPartOf>\n')

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
