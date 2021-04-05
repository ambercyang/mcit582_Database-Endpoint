#!/usr/bin/env python
# coding: utf-8

# In[1]:


#pip install flask_restful
#pip install py-algorand-sdk

from flask import Flask, request, g
from flask_restful import Resource, Api
from sqlalchemy import create_engine, select, MetaData, Table
from flask import jsonify
import json
import eth_account
import algosdk
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import load_only


# In[2]:


# In[3]:


from models import Base, Order, Log
engine = create_engine('sqlite:///orders.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

app = Flask(__name__)

#These decorators allow you to use g.session to access the database inside the request code
@app.before_request
def create_session():
    g.session = scoped_session(DBSession) #g is an "application global" https://flask.palletsprojects.com/en/1.1.x/api/#application-globals

@app.teardown_appcontext
def shutdown_session(response_or_exc):
    g.session.commit()
    g.session.remove()

"""
-------- Helper methods (feel free to add your own!) -------
"""


# In[4]:


def log_message(d):
    # Takes input dictionary d and writes it to the Log table
    order =  json.dumps(d)
    #log_obj = Log(sender_pk=order['sender_pk'],receiver_pk=order['receiver_pk'], \
    #          buy_currency=order['buy_currency'], sell_currency=order['sell_currency'], \
    #          buy_amount=order['buy_amount'], sell_amount=order['sell_amount'] )
    g.session.add(Log(message=order))
    g.session.commit()
  
    pass

"""
---------------- Endpoints ----------------
"""


@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount"]
        fields = [ "sig", "payload" ]
        error = False
        for field in fields:
            if not field in content.keys():
                print( f"{field} not received by Trade" )
                print( json.dumps(content) )
                log_message(content)
                return jsonify( False )
        
        error = False
        for column in columns:
            if not column in content['payload'].keys():
                print( f"{column} not received by Trade" )
                error = True
        if error: 
            print( json.dumps(content) )
            log_message(content)
            return jsonify( False )
            
        #Your code here
        #Note that you can access the database session using g.session
        sk = content['sig']
        payload = content['payload']
        
        order = {}
        order['sender_pk'] = payload['sender_pk']
        order['receiver_pk'] = payload['receiver_pk']
        order['buy_currency'] = payload['buy_currency']
        order['sell_currency'] = payload['sell_currency']
        order['buy_amount'] = payload['buy_amount']
        order['sell_amount'] = payload['sell_amount']
        order['signature'] = sk
        

        order_obj = Order( sender_pk=order['sender_pk'],receiver_pk=order['receiver_pk'],                          buy_currency=order['buy_currency'], sell_currency=order['sell_currency'],                           buy_amount=order['buy_amount'], sell_amount=order['sell_amount'],signature = order['signature'])

        g.session.add(order_obj)
        #g.session.add( Order(**order) )
        g.session.commit()
        return jsonify( True )


        
        


# In[ ]:


@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session   
    temp = g.session.query(Order)
    mydict = []
    for myquery in temp.all():
        order = {}
        order['buy_currency'] = getattr(myquery,'buy_currency')
        order['sell_currency'] =  getattr(myquery,'sell_currency')
        order['buy_amount'] =  getattr(myquery,'buy_amount')
        order['sell_amount'] =  getattr(myquery,'sell_amount')
        order['sender_pk'] =  getattr(myquery,'sender_pk')
        order['receiver_pk'] =  getattr(myquery,'receiver_pk')
        order['signature'] =  getattr(myquery,'signature')
        mydict.append(order)
    result = { 'data': mydict } 
    print(result) 
    return jsonify(result)

if __name__ == '__main__':
    app.run(port='5002')


# In[ ]:


'''
orders=
{'sig': signature,
 'payload': { 'sender_pk': public_key,
             'receiver_pk': public_key,
            'buy_currency': "Ethereum",
            'sell_currency': "Algorand",
            'buy_amount': 51,
            'sell_amount': 257,
            'platform': 'Algorand'
            }
'''


# In[ ]:


'''
{'data': 
  {'sender_pk':'...',
   'receiver_pk':'...',
   'buy_currency':'...',
   'sell_currency':'...',
   'buy_amount':'...',
   'sell_amount':'...'}, 
  {'sender_pk':'...',
   'receiver_pk':'...',
   'buy_currency':'...',
   'sell_currency':'...',
   'buy_amount':'...',
   'sell_amount':'...'},
  ...
  {'sender_pk':'...',
   'receiver_pk':'...',
   'buy_currency':'...',
   'sell_currency':'...',
   'buy_amount':'...',
   'sell_amount':'...'}
]}
'''

