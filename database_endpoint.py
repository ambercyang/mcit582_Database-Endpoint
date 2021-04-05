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


run models.py


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


# In[5]:


def verify():
    result = False
    content = request.get_json(silent=True)    
    sk = content['sig']
    payload = content['payload']
    platform = content['payload']['platform']
    message = json.dumps(payload)
    pk = payload['pk']
    
    #1. Verifying an endpoint for verifying signatures for ethereum
    if platform == "Ethereum":
        eth_encoded_msg = eth_account.messages.encode_defunct(text=message) 
        recovered_pk = eth_account.Account.recover_message(eth_encoded_msg,signature=sk)
        if(recovered_pk ==pk):
            result = True
            print( "Eth sig verifies!" )    
    
    #2. Verifying an endpoint for verifying signatures for Algorand
    elif platform == "Algorand":
        result = algosdk.util.verify_bytes(message.encode('utf-8'),sk,pk)
        if(result):
            print( "Algo sig verifies!" )
    
    #3. Check for invalid input
    else:
        print("invalid input")

    #Check if signature is valid
    #result = True #Should only be true if signature validates
    return jsonify(result)


# In[6]:


@app.route('/trade', methods=['POST'])
def trade():
    if request.method == "POST":
        content = request.get_json(silent=True)
        print( f"content = {json.dumps(content)}" )
        columns = [ "sender_pk", "receiver_pk", "buy_currency", "sell_currency", "buy_amount", "sell_amount", "platform" ]
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
        g.session.commit()
        return jsonify( True )


        
        


# In[ ]:


@app.route('/order_book')
def order_book():
    #Your code here
    #Note that you can access the database session using g.session   
    temp = g.session.query(Order)
    mydict = []
    for sqlrs in temp.all():
        order = {}
        order['buy_currency'] = getattr(sqlrs,'buy_currency')
        order['sell_currency'] =  getattr(sqlrs,'sell_currency')
        order['buy_amount'] =  getattr(sqlrs,'buy_amount')
        order['sell_amount'] =  getattr(sqlrs,'sell_amount')
        order['sender_pk'] =  getattr(sqlrs,'sender_pk')
        order['receiver_pk'] =  getattr(sqlrs,'receiver_pk')
        order['signature'] =  getattr(sqlrs,'signature')
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

