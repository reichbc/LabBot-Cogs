from redbot.core.bot import Red

from .linkcleaner import LinkCleaner

def setup(bot):
    bot.add_cog(LinkCleaner(bot))

