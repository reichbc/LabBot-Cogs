import json
import os
import re
from urllib.parse import urlparse, urlunparse
from redbot.core import commands

class LinkCleaner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.settings = self.load_settings()
        self.regex_pattern = self.build_regex_pattern()

    def load_settings(self):
        # Load settings from settings.json
        settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
        with open(settings_path, "r") as f:
            return json.load(f)

    def build_regex_pattern(self):
        # Dynamically create a regex pattern based on domains in settings.json
        domains = self.settings.get("whitelist_domains", [])
        domain_pattern = "|".join([re.escape(domain) for domain in domains])
        return rf"(https?://(?:www\.)?(?:{domain_pattern})/[^\s]+)"

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Find all URLs matching the dynamically generated regex
        urls = re.findall(self.regex_pattern, message.content)
        if not urls:
            return

        cleaned_message = message.content
        cleaned_links = []
        modified = False

        for url in urls:
            parsed_url = urlparse(url)
            
            # Only clean links if they have a query string
            if parsed_url.query:
                # Remove the query string from the URL
                cleaned_url = urlunparse(parsed_url._replace(query=""))
                cleaned_message = cleaned_message.replace(url, cleaned_url)
                cleaned_links.append(cleaned_url)
                modified = True

        # If the message was modified (i.e., any URL had a query string), delete the original message and repost
        if modified:
            await message.delete()

            response = f"The link pasted by <@{message.author.id}> has been deleted due to containing a user-tracking query string."

            # Quote the original message if there was additional text besides the link
            if message.content.strip() != url:
                user_text = f"<@{message.author.id}> said: \"{message.content.strip()}\""
                response += f"\n\n{user_text}"

            response += f"\n\n{' '.join(cleaned_links)}"
            await message.channel.send(response)
