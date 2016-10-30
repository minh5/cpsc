import pandas as pd

import plotly.plotly as py
import plotly.graph_objs as go
import plotly.tools as tls

class cleaner(object):
    
    def __init__(self, data):
        self.data = data
    
    @staticmethod
    def append_string(append_type, row):
        if append_type == 'hospital':
            return 'hosp_' + row['psu'].__str__()
        elif append_type == 'product':
            return 'product_' + row['prod1'].__str__()
        else:
            raise Exception('not valid append type')

    @staticmethod
    def recode_race(row):
        if row['race'] == 1:
            return 'white'
        elif row['race'] == 2:
            return 'black'
        elif row['race'] == 3 and row['race_other'] == 'HISPANIC':
            return 'hispanic'
        else:
            return 'other'
     
    @staticmethod
    def recode_stratum(row, stratum):
        if row['stratum'] == stratum:
            return 1
        else:
            return 0
    
    @property
    def processed_data(self):
        data = self.data
        data['hospital'] = data.apply(lambda x: self.append_string('hospital', x), axis=1)
        data['product'] = data.apply(lambda x: self.append_string('product', x), axis=1)
        data['new_race'] = data.apply(lambda x: self.recode_race(x), axis=1)
        for stratum in ['C', 'S', 'M', 'L', 'V']:
            data['stratum_' + stratum] = data.apply(lambda x: self.recode_stratum(x, stratum), axis=1)
        return data
    
    @property
    def crosstab(self):
        grouped = pd.crosstab(self.data['hospital'], self.data['product'])
        return grouped
        
class query(object):
    
    def __init__(self, cleaned_data, crosstab):
        self.data = cleaned_data
        self.crosstab = crosstab
        
    def retrieve_query(self, group_name, group_value, query_name, top_num=9):
        data = self.data
        subset = data.ix[data[group_name] == group_value, query_name].value_counts()[0:top_num]
        return subset

    def get_product_by_hospital(self, hospital_name, top_num=9):
        return self.retrieve_query(group_name='hospital', group_value=hospital_name,
                                   query_name='product', top_num=top_num)
    
    def get_hospitals_by_product(self, product_name, top_num=9):
        return self.retrieve_query(group_name='product', group_value=product_name,
                                   query_name='hospital', top_num=top_num)
    
    def get_product_by_size(self, stratum_value, top_num=9):
        return self.retrieve_query(group_name='stratum', group_value=stratum_value,
                                  query_name='product', top_num=top_num)
    
    def get_counts(self, count_type, product_num=None, hosp_name=None):
        if count_type == 'product':
            return self.crosstab.ix[:, product_num]
        elif count_type == 'hospital':
            return self.crosstab.ix[hosp_name,:]
        else:
            raise Exception('invalid count type input')
            
    def product_counts(self, product_num):
        return self.get_counts('product', product_num=product_num)
    
    def hospital_counts(self, hosp_name):
        return self.get_counts('hospital', hosp_name=hosp_name)
    
    def plot_product(self, product_num):
        data = self.product_counts(product_num)
        graph = [go.Bar(
            x=self.crosstab.index.values.tolist(),
            y=data.values,
        )]
        layout = go.Layout(title='Hospital Records for Product - ' + product_num)
        fig = go.Figure(data=graph, layout=layout)
        return py.iplot(fig)
    
    def plot_hospital(self, hosp_name):
        data = self.hospital_counts(hosp_name)
        graph = [go.Bar(
            x=self.crosstab.columns.values.tolist(),
            y=data.values,
        )]
        layout = go.Layout(title='Product Counts for Hospital - ' + hosp_name)
        fig = go.Figure(data=graph, layout=layout)
        return py.iplot(fig)
    
    def get_top_product(self, hospital_name):
        return self.data.ix[self.data['hospital'] == hospital_name, 'product'].value_counts().index[0]
    
    def top_product_for_hospital(self):
        hosp_dict = {}
        for hospital in self.data.hospital.value_counts().index:
            hosp_dict[hospital] = self.get_top_product(hospital)
        return pd.Series([val for val in hosp_dict.values()]).value_counts() 
    
    def prepare_stratum_modeling(self, product):
        counts = self.data.ix[self.data['product'] == product,:]['hospital'].value_counts()
        product_df = pd.DataFrame(counts)
        columns = ['hospital', 'stratum_C', 'stratum_S', 'stratum_M', 'stratum_L', 'stratum_V']
        df = pd.merge(product_df, self.data.ix[:, columns], left_index=True, right_on=['hospital'], how='left')
        return df

    def prepare_stratum_modeling2(self, product):
        counts = self.data.ix[self.data['product'] == product,:]['hospital'].value_counts()
        product_df = pd.DataFrame(counts)

        df = pd.merge(product_df, self.data.ix[:, ['hospital' ,'stratum']], left_index=True, right_on=['hospital'], how='left')
        return df