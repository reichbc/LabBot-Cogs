import re
from urllib.parse import urlparse, urlunparse
from redbot.core import commands

class LinkCleaner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Regex to match Amazon or eBay URLs
    AMAZON_EBAY_REGEX = r"(https?://(?:www\.)?(?:amazon|ebay)\.(?:com|co\.uk|ca|de|fr|it|es|nl|jp|in)/[^\s]+)"
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot's own messages or other bots
        if message.author.bot:
            return

        # Find all Amazon/eBay links in the message
        urls = re.findall(self.AMAZON_EBAY_REGEX, message.content)
        
        if not urls:
            return

        # Prepare a new message with cleaned links
        cleaned_message = message.content
        cleaned_links = []
        for url in urls:
            parsed_url = urlparse(url)
            # Remove the query string from the URL
            cleaned_url = urlunparse(parsed_url._replace(query=""))
            cleaned_message = cleaned_message.replace(url, cleaned_url)
            cleaned_links.append(cleaned_url)

        # If the message was modified, delete the original and re-post it
        if cleaned_message != message.content:
            # Delete the original message
            await message.delete()

            # Repost the notification with cleaned URLs
            response = (
                f"The link pasted by <@{message.author.id}> has been deleted due to containing a user-tracking query string."
            )

            # Include any additional text the user might have added, or just the cleaned links
            if message.content.strip() != url:
                user_text = f"<@{message.author.id}> said: \"{message.content.strip()}\""
                response += f"\n\n{user_text}"

            # Add cleaned links to the response
            response += f"\n\n{' '.join(cleaned_links)}"

            # Send the response to the channel
            await message.channel.send(response)

# Add the cog to the bot
def setup(bot):
    bot.add_cog(LinkCleaner(bot))
