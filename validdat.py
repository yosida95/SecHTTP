#coding:utf-8
from bs4 import BeautifulSoup
import page_id_maker
import urlparse

class ValidDat:
    def valid(self,html,base_uri):
        self.base_uri = base_uri
        self.soup = BeautifulSoup(html)

        self.remove_tag('script')
        self.remove_tag('object')
        self.remove_tag('iframe')
        
        self.unwrap_tag('noscript')

        self.page_uri_lst = list()
        self.page_id_lst = list()

        #a
        a_list = self.soup.find_all('a')
        self.change_link(a_list,'href')

        #link
        link_list = self.soup.find_all('link')
        self.change_link(link_list,'href')

        #form
        form_list = self.soup.find_all('form')
        self.change_link(form_list,'action')

        #img
        img_list = self.soup.find_all('img')
        self.change_link(img_list,'src')

        #meta
        meta_list = self.soup.find_all('meta')
        self.change_link(meta_list,'content')

        #span
        span_list = self.soup.find_all('span')
        self.change_link(span_list,'data-href')
       
        return self.soup.prettify(),self.page_id_lst,self.page_uri_lst

    def change_link(self,tag_list,change_attribute):
        for tag in tag_list:
            try:
                uri=tag[change_attribute]
            except KeyError:
                continue

            if not uri in self.page_uri_lst:
                page_id = page_id_maker.make()
                next_uri=urlparse.urljoin(self.base_uri,uri)
                next_uri_scheme = urlparse.urlparse(next_uri).scheme
                #if ex)mailto:
                if not (next_uri_scheme=='http' or next_uri_scheme=='https'):
                    continue

                self.page_id_lst.append(page_id)
                self.page_uri_lst.append(next_uri)
                #change_tag
                tag[change_attribute]='../'+page_id
            else:
                next_uri=urlparse.urljoin(self.base_uri,uri)
                page_id = self.page_id_lst[self.page_uri_lst.index(next_uri)]
                tag[change_attribute]='../'+page_id

    def remove_tag(self,tag_name):
        tag_list = self.soup.find_all(tag_name)
        for tag in tag_list:
            tag.extract()
        
    def unwrap_tag(self,tag_name):
        tag_list = self.soup.find_all(tag_name)
        for tag in tag_list:
            tag.unwrap()

