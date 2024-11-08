
# EECE 351 Project Phase 1

## Welcome to AUBoutique!

Do you want to get some notebooks? Ae you interested in  collecting beautiful and well-designed craftwork? If the answer is yes, then you have reached your destination! AUBoutique, your new first choice shopping destination, is the answer! Imagine getting into this magnificent realm, where the pages of the notebook wave to you from the virtual shelves, and the craftwork beckons with artistic allure... All of that just a click away! And to provide such elegant features, the client-server architecture had a massive role in doing so. Users log in using their credentials, and can register a new account in case they were new. And after that, the clients are free to choose the option that they desire, from viewing all products, products of specific sellers, and so on. And if you want to list your products for sale, you are free to do so. But, perhaps, what makes this digital marketplace fascinating is the real-time texting between the clients and the sellers, where clients can initiate live chats with the sellers in case they had any questions about their products. This will help clients get clarifications about products they want, making them satisfied and happy with their decision. And once all is clear, the client can buy the available product and will receive a confirmation  message from the AUB Post Office to collect their items on a specified date. This is only the beginning, and hopefully, AUBoutique will become more popular and successful, bolstered with new exciting features! So what are you still waiting for? Enter the website and start your digital shopping journey and have fun!
	
## How to Run the Code

### Running the Server
To run the server, run:
		
	cd server
	python main.py PORT
where `PORT` is the port you wish to run the server on
		
### Running the Client
To run the client, run:
		
	cd client
	python client.py
		
## Dependencies

Once you run the code, you will have the option to log in if you already have an account, or register if not. After that, all options, such as ways of viewing products, selling, and buying, are clearly explained to the user. To download required dependencies, run this command:

	pip install -r requirements.txt