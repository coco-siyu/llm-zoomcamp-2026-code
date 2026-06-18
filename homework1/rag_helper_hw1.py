INSTRUCTIONS = '''
Your task is to answer questions from the course participants
based on the provided context.

Use the context to find relevant information and provide accurate
answers. If the answer is not found in the context,
respond with "I don't know."
'''
 
PROMPT_TEMPLATE = '''
QUESTION: {question}

CONTEXT:
{context}
'''.strip()


class RAGBase:

    def __init__(
        self,
        index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        model='gpt-5.4-mini'
    ):
        self.index = index
        self.llm_client = llm_client
        self.instructions = instructions

        self.prompt_template = prompt_template
        self.model = model

    def search(self, query):
        return self.index.search(
            query=query,
            num_results=5
    )

    def build_context(self, search_results):
        context = ""

        for doc in search_results:
                context += f"""
        filename: {doc['filename']}
        content:
        {doc['content']}

        """
        return context

    def build_prompt(self, query, search_results):
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )

    def llm(self, prompt):
        response = self.llm_client.responses.create(
        model=self.model,
        input=prompt,
    )

        return response # return the entire response

    def rag(self, query):
        # 3 components
        search_results = self.search(query)
        context = self.build_context(search_results)

        prompt = self.prompt_template.format(
            question=query,
            context=context
        )

        response = self.llm(prompt)
        answer = response.output_text

        prompt_tokens = response.usage.input_tokens
        return answer, prompt_tokens
    
class OllamaRag(RAGBase):
        def llm(self, prompt):
            input_messages = [
                {'role': 'developer', 'content': self.instructions},
                {'role': 'user', 'content': prompt}
        ]

            response = self.llm_client.responses.create(
                model = self.model,
                input = input_messages
            )

            return response.output_text