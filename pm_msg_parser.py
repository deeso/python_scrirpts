import re
import os

BEGIN_EMAIL_HEADERS = '-----BEGIN EMAIL HEADERS-----'
END_EMAIL_HEADERS = '-----BEGIN EMAIL HEADERS-----'

BEGIN_ATTACHMENTS = '-----BEGIN ATTACHMENTS-----'
END_ATTACHMENTS = '-----END ATTACHMENTS-----'

BEGIN_EMAIL_HEADERS = '-----BEGIN EMAIL HEADERS-----'
END_EMAIL_HEADERS = '-----END EMAIL HEADERS-----'

BEGIN_REPORT_COUNT = '-----BEGIN REPORT COUNT-----'
END_REPORT_COUNT = '-----END REPORT COUNT-----'

BEGIN_URLS = '-----BEGIN URLS-----'
END_URLS = '-----END URLS-----'


class Base(object):
    HEADERS_RE = re.compile('^[\w-]+: ')

    @classmethod
    def find_start(cls, content):
        return content.find(cls.BEGIN)

    @classmethod
    def find_end(cls, content):
        return content.find(cls.END)

    def __init__(self, content):
        self.content = content
        self.start = EmailHeaders.find_start(self.BEGIN)
        self.end = EmailHeaders.find_end(self.END)

        self.data = None
        if self.start > -1 and self.end > -1 and self.start < self.end:
            d = self.content.split(self.BEGIN)[1]
            d = d.split(self.END)[0].strip()
            self.data = d

        self.headers = set()
        self.extracted_values = []
        self.extracted_values_by_header = {}

    def parse_headers(self):
        r = self.HEADERS_RE
        lines = [i.strip()
                 for i in self.data.splitlines()
                 if len(i.strip()) > 0]
        # laziness of completeness
        # pos = 0
        # end = len(lines)
        # while pos < end:
        #     line = lines[pos]
        #     pos += 1
        last_value = None
        last_header = None
        for line in lines:
            s = r.match(line)
            if s is not None:
                if last_value is not None:
                    lhl = last_header.lower()
                    if last_header not in self.extracted_values_by_header:
                        self.extracted_values_by_header[lhl] = []

                    self.extracted_values.append((last_header, last_value))
                    self.extracted_values_by_header[lhl].append(last_value)
                    last_value = None
                    last_header = None

                last_header = s.group().rstrip(': ')
                last_value = line.lstrip()
            else:
                last_value += "\n" + line

        if last_value is not None:
            if last_header not in self.extracted_values_by_header:
                self.extracted_values_by_header[last_header] = []

            self.extracted_values.append((last_header, last_value))
            self.extracted_values_by_header[last_header].append(last_value)

        return self.extracted_values

    def has_header(self, header):
        return header in self.extracted_values_by_header

    def get_header_values(self, header):
        return self.extracted_values_by_header[header]


class EmailHeaders(Base):
    BEGIN = '-----BEGIN EMAIL HEADERS-----'
    END = '-----END EMAIL HEADERS-----'

    def __init__(self, content):
        Base.__init__(self, content)


class Urls(Base):
    BEGIN = '-----BEGIN URLS-----'
    END = '-----END URLS-----'
    URL_HEADER = 'URL'
    DOMAIN_HEADER = 'URL Domain'
    LINK_TEXT_HEADER = 'Link text'

    def __init__(self, content):
        Base.__init__(self, content)

    def get_url_counts(self):
        urls = {}
        if not self.has_header(self.URL_HEADER):
            return urls

        for url in self.extracted_values_by_header[self.URL_HEADER]:
            u = url.replace(' ', '')
            if u not in urls:
                urls[u] = 0
            urls[u] += 1
        return urls

    def get_domains(self):
        domains = {}
        if not self.has_header(self.DOMAIN_HEADER):
            return domains

        for domain in self.extracted_values_by_header[self.DOMAIN_HEADER]:
            if domain not in domains:
                domains[domain] = 0
            domains[domain] += 1
        return domains

    def get_link_text(self):
        if not self.has_header(self.LINK_TEXT_HEADER):
            return []
        return [i for i in self.extracted_values_by_header[self.LINK_TEXT_HEADER]]


class Attachments(Base):
    BEGIN = '-----BEGIN ATTACHMENTS-----'
    END = '-----END ATTACHMENTS-----'
    FILE_NAME_HEADER = 'File Name'

    def __init__(self, content):
        Base.__init__(self, content)

    def get_file_counts(self):
        exts = {'names': [], 'exts': {}}
        if not self.has_header(self.FILE_NAME_HEADER):
            return exts

        for fname in self.extracted_values_by_header[self.FILE_NAME_HEADER]:
            _, ext = os.path.splitext(fname)
            if ext not in exts['exts']:
                exts['exts'][ext] = 0
            exts['exts'][ext] += 1
            exts['names'].append(fname)
        return exts


class ReportCount(Base):
    BEGIN = '-----BEGIN REPORT COUNT-----'
    END = '-----END ATTACHMENTS-----'

    def __init__(self, content):
        Base.__init__(self, content)


class Body(object):
    BODY_REPORTED_AGENT = 'Body : Reporter agent: '

    def __init__(self, content):
        self.content = content
        if self.content.find(Body.BODY_REPORTED_AGENT) != 0:
            raise Exception("Unable to parse current body, unexpected header")

        self.body_info = content.splitlines()[0].strip()
        self.email_headers = EmailHeaders(content)
        self.urls = Urls(content)
        self.attachments = Attachments(content)
        self.report_counts = ReportCount(content)

class Bodys(object):
    BODY_REPORTED_AGENT = 'Body : Reporter agent: '

    def __init__(self, content):
        self.content = content
        bodys = [self.BODY_REPORTED_AGENT + i
                 for i in content.split(Body.BODY_REPORTED_AGENT)]

        quick_list = lambda b: [i.strip() for i in b.split('\r\n') if len(i.strip()) > 0 ]
        body_transform = lambda b: "\n".join(quick_list(b))
        self.body_contents = [body_transform(b) for b in bodys]
        self.bodys = [Body(i) for i in self.body_contents]
