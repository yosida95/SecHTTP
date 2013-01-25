#coding:utf-8
from bs4 import BeautifulSoup
import page_id_maker
import urlparse
import cssutils
from cssutils.css import CSSImportRule,CSSComment,CSSStyleRule
import logging


class URIListmaker:
    def page_uri_lister(self,uri,base_uri,page_id_lst,page_uri_lst):

        if not uri in page_uri_lst:
            page_id = page_id_maker.make()
            next_uri=urlparse.urljoin(base_uri,uri)
            next_uri_scheme = urlparse.urlparse(next_uri).scheme
            #if ex)mailto:
            if not (next_uri_scheme=='http' or next_uri_scheme=='https'):
                return page_id_lst,page_uri_lst,False

            page_id_lst.append(page_id)
            page_uri_lst.append(next_uri)
        else:
            next_uri=urlparse.urljoin(base_uri,uri)
            page_id = page_id_lst[page_uri_lst.index(next_uri)]
        self.page_id_lst = page_id_lst
        self.page_uri_lst = page_id_lst

        return page_id_lst,page_uri_lst,page_id

    #ugly
    def uri_replacer(self,uri,base_uri):
        self.page_id_lst,self.page_uri_lst,self.page_id = self.page_uri_lister(uri,base_uri,self.page_id_lst,self.page_uri_lst)
        if self.page_id==False:
            return uri
        else:
            return '../'+self.page_id



class Html(URIListmaker):
    def valid(self,html,base_uri):
        self.base_uri = base_uri
        self.soup = BeautifulSoup(html)

        self.remove_tag('script')
        self.remove_tag('object')
        self.remove_tag('iframe')
        
        self.unwrap_tag('noscript')

        self.page_uri_lst = list()
        self.page_id_lst = list()
        self.base_uri=base_uri

        #a
        a_list = self.soup.find_all('a',href=True)
        self.change_link(a_list,'href')

        #link
        link_list = self.soup.find_all('link',href=True)
        self.change_link(link_list,'href')

        #form
        form_list = self.soup.find_all('form',action=True)
        self.change_link(form_list,'action')

        #img
        img_list = self.soup.find_all('img',src=True)
        self.change_link(img_list,'src')

        #meta
        meta_list = self.soup.find_all('meta',content=True)
        self.change_link(meta_list,'content')

        #span
        span_list = self.soup.find_all('span')
        self.change_link(span_list,'data-href')

        style_list = self.soup.find_all('style')
        self.change_inline_style(style_list)
       
        return self.soup.prettify(),self.page_id_lst,self.page_uri_lst

    def change_link(self,tag_list,change_attribute):
        for tag in tag_list:
            try:
                uri=tag[change_attribute]
            except KeyError:
                continue
            new_page_id_lst,new_page_uri_lst,page_id = self.page_uri_lister(uri,self.base_uri,self.page_id_lst,self.page_uri_lst)
            if page_id==False:
                #change_tag
                tag[change_attribute]=uri
            else:
                #change_tag
                tag[change_attribute]='../'+page_id
            self.page_id_lst=new_page_id_lst
            self.page_uri_lst=new_page_uri_lst

    def remove_tag(self,tag_name):
        tag_list = self.soup.find_all(tag_name)
        for tag in tag_list:
            tag.extract()
        
    def unwrap_tag(self,tag_name):
        tag_list = self.soup.find_all(tag_name)
        for tag in tag_list:
            tag.unwrap()

    def change_inline_style(self,tag_list):
        for tag in tag_list:
            css_dat=tag.string
            cssvalider = Css()
            inline=True
            validated_css,page_id_lst,page_uri_lst = cssvalider.valid(css_dat,self.base_uri,self.page_id_lst,self.page_uri_lst,inline)
            tag.string=validated_css
            self.page_id_lst=page_id_lst
            self.page_uri_lst=page_uri_lst
            

class Css(URIListmaker):
    def valid(self,page_data,base_uri,page_id_lst=None,page_uri_lst=None,inline=False):
        if inline:
            self.page_id_lst=page_id_lst
            self.page_uri_lst=page_uri_lst
        else:
            self.page_id_lst=list()
            self.page_uri_lst=list()

        cssutils.log.setLevel(logging.CRITICAL)
        cssutils.cssproductions.MACROS['name'] = r'[\*]?{nmchar}+'

        try:
            sheet = cssutils.parseString(page_data)
        except:
            sheet = cssutils.css.CSSStyleDeclaration(cssText=page_data)

        cssutils.replaceUrls(sheet,lambda url: self.uri_replacer(url,base_uri))
        return sheet.cssText,self.page_id_lst,self.page_uri_lst
    

