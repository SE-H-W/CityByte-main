# from django.contrib.auth.forms import UserCreationForm
# from django.urls import reverse_lazy
# from django.views import generic
 
 
# class SignUpView(generic.CreateView):
#     form_class = UserCreationForm
#     success_url = reverse_lazy("login")
#     template_name = "registration/signup.html"

from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.shortcuts import render
 
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import render
from django.shortcuts import render
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os
import markdown
from django.shortcuts import render
from info.helpers.newsapi_helper import NewsAPIHelper


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class CustomPasswordResetView(PasswordResetView):
    def form_valid(self, form):
        print("Attempting to send password reset email...")
        return super().form_valid(form)
    
# Initialize the LLM with the Gemini API key
def initialize_gemini_llm():
    api_key = 'AIzaSyCQuxhdViKd_-H1CQxEpFsgsHEolKLEN7w' # Fetch the key from an environment variable
    if not api_key:
        raise Exception("Gemini API Key not set. Please configure the key.")
    
    # Set up the Gemini LLM
    my_llm = ChatGoogleGenerativeAI(model='gemini-pro', api_key=api_key)
    return my_llm

def city_info(request, city_name):
    itinerary = None  # To store the generated itinerary
    if request.method == 'POST':
        # Get the number of days from the form input
        days = request.POST.get('days')

        # Initialize Gemini LLM
        my_llm = initialize_gemini_llm()

        # Create a prompt template with placeholders for the city and number of days
        my_prompt = PromptTemplate.from_template('Create an itinerary for {placename} for {num} days')
        
        # Create the chain
        chain = LLMChain(llm=my_llm, prompt=my_prompt, verbose=False)
        
        # Define both place and num
        inputs = {'placename': city_name, 'num': days}
        
        # Invoke the chain with both inputs
        response = chain.invoke(input=inputs)
        
        # Get the response text from the LLM
        itinerary = response

        itinerary=itinerary['text']

        itinerary=markdown.markdown(itinerary)
        
        return render(request, 'info/itinerary.html', {
            'city': city_name,
            'itinerary': itinerary
        })
    
def city_news(request, city, country):
    news_api_helper = NewsAPIHelper()
    news_articles = news_api_helper.get_city_news(city)

    context = {
        "city": city,
        "country": country,
        "news_articles": news_articles
    }
    return render(request, "info/news.html", context)