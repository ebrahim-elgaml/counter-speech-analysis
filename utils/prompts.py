
SYSTEM_MESSAGE = """
    Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
    Here are the definitions::
        * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
        * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
        * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.
"""

prompts = {
    "gpt_single_system_message": """
        Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
        Here are the definitions::
            * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
            * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
            * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.
        
        The input will be a parent speech and a counter speech to the parent speech with the following format:
    Parent speech: {parent speech}
    Counter speech: {respond speech}

    You have to do the following
    1. Determine if parent speech is a hate speech or a neutral speech given the mentioned definitions
    2. Determine if the counter speech is counter hate speech, hate speech or neutral speech based on the mentioned definition before for each one.
    ----------------------------------
    Example scenarios to consider for illustration and learn how to determine the type of speech:
    Scenario 1:
    Parent speech: This is the type of thinking that make people afraid to come out about sexual assault. It's how people rationalize assault by a close peer. You weren't raped honey, you just regret it. Are you sure you didn't flirt with him? How can you be sure you didn't lead him on? It's all a way to cover up what happened.   False accusations are a heinous thing, as someone who would rather let criminals walk than see an innocent be jailed. But encouraging the suppression of sexual assault reporting by supporting the "regret doesn't equal rape" narrative is fucked up. 
    Counter speech: So regret *does* equal rape?
    
    Response: Parent speech is neutral speech, Counter speech is hate speech

    Scenario 2:
    Parent speech: The girl should be put in jail and given the same punishment a rapist would get
    Counter speech: But that would discourage other women from lying about rape.

    Response: Parent speech is hate speech, Counter speech is counter hate speech

    Scenario 3:
    Parent speech: just think how great a place to work it will be? cheaters, liars, narcissist and huge twats all working together.  i hope she is successful and creates her own personal hell on earth 
    Counter speech: > cheaters, liars, narcissist and huge twats all working together.  A perfect synopsis of /r/politics 
    
    Response: Parent speech is hate speech, Counter speech is hate speech


    Scenario 4:
    Parent speech: A great friend of mine trained  her husband to piss sitting down.  I visited and got up to piss at night.  Got read the Riot Act in the morning because she fell in.  It came out he had to piss sitting, and I couldn't  help just [hee hawing.](https://www.youtube.com/watch?v=FopyRHHlt3M)  Now I feel sad.
    Counter speech: My solution to this: piss in the sink, only use toilet to number 2.

    Response: Parent speech is neutral speech, Counter speech is neutral speech
    ----------------------------------
    
    Please reply with the following format:
    Parent speech is [your evaluation], Counter speech is [your evaluation], because [your explanation]
    

    Please note that your evaluation can be one of the following: hate speech, counter hate speech, neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """,
    "gpt_single_prompt": """
    Parent speech: {parent_speech}
    Counter speech: {counter_speech}
    """,
    "gpt_multi_system_message": """
        Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
        Here are the definitions::
            * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
            * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
            * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.

    I will share with you first a parent speech and you have to evaluate if the provided speech is a hate speech or a neutral speech. After that I will ask you about the counter speech.
    If the parent speech is a hate speech, your job will be to evaluate if the provided speech is a hate speech, counter hate speech for the parent speech or neutral speech. 
    If the parent speech is a neutral speech, your job will be to evaluate if the provided speech is a hate speech or neutral speech based 
    """,
    "gpt_multi_hate_prompt": """
    Is this speech '{speech}' a hate speech or a neutral speech based on the mentioned definitions?
    Please reply with the following format

    (your evaluation), because (your explanation)
    
    Please note that your evaluation can be one of the following: hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """,
    "gpt_multi_counter_prompt": """
        Is this speech '{counter_speech}' a hate speech or neutral speech or counter hate speech to the previous hate speech based on the mentioned definitions?
        Please reply with the following format
        (your evaluation), because (your explanation)
        Please note that your evaluation can be one of the following: counter hate speech, hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """,
    "gemini_single_prompt": """
            Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
            Here are the definitions::
                * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
                * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
                * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.

            The input will be a parent speech and a counter speech to the parent speech with the following format:
        Parent speech: (parent speech)
        Counter speech: (respond speech)

        You have to do the following
        1. Determine if parent speech is a hate speech or a neutral speech given the mentioned definitions
        2. Determine if the counter speech is counter hate speech, hate speech or neutral speech based on the mentioned definition before for each one.
        ----------------------------------
        Example scenarios to consider for illustration and learn how to determine the type of speech:
        Scenario 1:
        Parent speech: This is the type of thinking that make people afraid to come out about sexual assault. It's how people rationalize assault by a close peer. You weren't raped honey, you just regret it. Are you sure you didn't flirt with him? How can you be sure you didn't lead him on? It's all a way to cover up what happened.   False accusations are a heinous thing, as someone who would rather let criminals walk than see an innocent be jailed. But encouraging the suppression of sexual assault reporting by supporting the "regret doesn't equal rape" narrative is fucked up.
        Counter speech: So regret *does* equal rape?

        Response: Parent speech is neutral speech, Counter speech is hate speech

        Scenario 2:
        Parent speech: The girl should be put in jail and given the same punishment a rapist would get
        Counter speech: But that would discourage other women from lying about rape.

        Response: Parent speech is hate speech, Counter speech is counter hate speech

        Scenario 3:
        Parent speech: just think how great a place to work it will be? cheaters, liars, narcissist and huge twats all working together.  i hope she is successful and creates her own personal hell on earth
        Counter speech: > cheaters, liars, narcissist and huge twats all working together.  A perfect synopsis of /r/politics

        Response: Parent speech is hate speech, Counter speech is hate speech


        Scenario 4:
        Parent speech: A great friend of mine trained  her husband to piss sitting down.  I visited and got up to piss at night.  Got read the Riot Act in the morning because she fell in.  It came out he had to piss sitting, and I couldn't  help just [hee hawing.](https://www.youtube.com/watch?v=FopyRHHlt3M)  Now I feel sad.
        Counter speech: My solution to this: piss in the sink, only use toilet to number 2.

        Response: Parent speech is neutral speech, Counter speech is neutral speech

        Scenario 5:
        Parent speech: Yeah a fucking bullet to the head you fucking white male
        Counter speech: "You're fucking a white male!"

        Response: Parent speech is hate speech, Counter speech is hate speech
        ----------------------------------

        Please reply with the following format:
        Parent speech is (your evaluation), Counter speech is (your evaluation), because (your explanation)


        Please note that your evaluation can be one of the following: hate speech, counter hate speech, neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
        --------------------
        Parent speech: {parent_speech}
        Counter speech: {counter_speech}
    """,
    "gemini_multi_system_message": """
        Assume you are a bot that helps reduce hate on the internet. Your job to figure out if a speech can be considered as a hate speech, counter hate speech  to another speech or neutral speech based on the provided definitions.
        Here are the definitions:
            * Hate: Content that insults, expresses, incites, or promotes hate, violence or serious harm based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
            * Counter-hate: Content that is responding to hate speech with empathy and challenging the hate narratives or asking for clarification, rather than responding with more hate speech directed in the opposite direction.
            * Neutral speech: is a speech that can't be considered as a hate speech nor a counter hate speech.
    """,
    "gemini_multi_hate_prompt": """
        {system_message}
        I will share with you a speech and you have to evaluate if the provided speech is a hate speech or a neutral speech.

        --------------------------------
        Is this speech '{speech}' a hate speech or a neutral speech based on the mentioned definitions?
        Please reply with the following format

        (your evaluation), because (your explanation)

        Please note that your evaluation can be one of the following: hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """,
    "gemini_multi_counter_prompt": """
        {system_message}
        ------------------------------------------------

        Is this speech '{counter_speech}' a hate speech or neutral speech or counter hate speech to this hate speech '{parent_speech}' based on the mentioned definitions?
        Please reply with the following format
        (your evaluation), because (your explanation)
        Please note that your evaluation can be one of the following: counter hate speech, hate speech or neutral speech. The explanation should be a short explanation of your answer that consists of 1-2 sentences.
    """
}
