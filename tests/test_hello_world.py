"""
Test module for the HelloWorld class.

This module contains unit tests for the HelloWorld class functionality.
"""

from unittest import TestCase

from liquisketch.hello_world import HelloWorld


class TestHelloWorld(TestCase):
    """
    Test cases for the HelloWorld class.
    
    This class contains all unit tests for the HelloWorld functionality.
    """

    def test_greeting_response(self):
        """
        Test the basic greet method returns expected greeting.
        """
        hello_world = HelloWorld()

        result = hello_world.greet()

        self.assertEqual('Hello', result)

    def test_greeting_with_name(self):
        """
        Test the greet_with_name method returns personalized greeting.
        """
        hello_world = HelloWorld()

        result = hello_world.greet_with_name('World')

        self.assertEqual('Hello, World!', result)
