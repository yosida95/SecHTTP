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
        
        self.unwrap_tag('noscript')

        self.page_uri_lst = list()
        self.page_id_lst = list()

        #for_a
        a_list = self.soup.find_all('a')
        self.change_link(a_list,'href')

        #for_link
        link_list = self.soup.find_all('link')
        self.change_link(link_list,'href')

        #for_form
        form_list = self.soup.find_all('form')
        self.change_link(form_list,'action')

        #img
        img_list = self.soup.find_all('img')
        self.change_link(img_list,'src')
       
        return self.soup.prettify(),self.page_id_lst,self.page_uri_lst

    def change_link(self,tag_list,change_attribute):
        for tag in tag_list:
            uri=tag[change_attribute]
            if not uri in self.page_uri_lst:
                page_id = page_id_maker.make()
                self.page_id_lst.append(page_id)
                next_uri=urlparse.urljoin(self.base_uri,uri)
                self.page_uri_lst.append(next_uri)
                #change_a
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

