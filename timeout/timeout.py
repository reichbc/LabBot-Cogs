import datetime

import discord
from redbot.core import Config, checks, commands


class Timeout(commands.Cog):
    """Timeout a user"""

    def __init__(self):
        self.config = Config.get_conf(self, identifier=539343858187161140)
        default_guild = {
            "logchannel": "",
            "report": "",
            "timeoutrole": ""
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(
            roles=[]
        )

    # Helper functions

    async def report_handler(self, ctx: commands.Context, user: discord.Member, action_info: dict):
        """Build and send embed reports"""

        # Retrieve log channel
        log_channel_config = await self.config.guild(ctx.guild).logchannel()
        log_channel = ctx.guild.get_channel(log_channel_config)

        # Build embed
        embed = discord.Embed(
            description=f"{user.mention} ({user.id})",
            color=(await ctx.embed_colour()),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(
            name="Moderator",
            value=ctx.author.mention,
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=action_info["reason"],
            inline=False
        )

        if user.avatar_url:
            embed.set_author(
                name=f"{user} {action_info['action']} timeout",
                icon_url=user.avatar_url)
        else:
            embed.set_author(
                name=f"{user} {action_info['action']} timeout"
            )

        # Send embed
        await log_channel.send(embed=embed)

    async def timeout_add(self, ctx: commands.Context, user: discord.Member, reason: str, timeout_role: discord.Role):
        """Retrieve and save user's roles, then add user to timeout"""
        # Store the user's current roles
        user_roles = []
        for role in user.roles:
            user_roles.append(role.id)

        await self.config.member(user).roles.set(user_roles)

        # Replace all of a user's roles with timeout role
        try:
            await user.edit(roles=[timeout_role])
        except AttributeError:
            await ctx.send("Please set the timeout role using `[p]timeoutset role`.")
            return
        except discord.Forbidden:
            await ctx.send("Whoops, looks like I don't have permission to do that.")
            return
        except discord.HTTPException as error:
            await ctx.send("Something went wrong!")
            raise Exception(error) from error
        else:
            await ctx.message.add_reaction("✅")

            # Send report to channel
            if await self.config.guild(ctx.guild).report():
                action_info = {
                    "reason": reason,
                    "action": "added to"
                }
                await self.report_handler(ctx, user, action_info)

    async def timeout_remove(self, ctx: commands.Context, user: discord.Member, reason: str):
        """Remove user from timeout"""
        # Fetch and define user's previous roles.
        user_roles = []
        for role in await self.config.member(user).roles():
            user_roles.append(ctx.guild.get_role(role))

        # Replace user's roles with their previous roles.
        try:
            await user.edit(roles=user_roles)
        except discord.Forbidden:
            await ctx.send("Whoops, looks like I don't have permission to do that.")
        except discord.HTTPException as error:
            await ctx.send("Something went wrong!")
            raise Exception(error) from error
        else:
            await ctx.message.add_reaction("✅")

            # Clear user's roles from config
            await self.config.member(user).clear()

            # Send report to channel
            if await self.config.guild(ctx.guild).report():
                action_info = {
                    "reason": reason,
                    "action": "removed from"
                }
                await self.report_handler(ctx, user, action_info)

    # Commands

    @commands.guild_only()
    @commands.group()
    async def timeoutset(self, ctx: commands.Context):
        """Change the configurations for `[p]timeout`."""
        if not ctx.invoked_subcommand:
            pass

    @timeoutset.command(name="logchannel")
    @checks.mod()
    async def timeoutset_logchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the log channel for any reports etc.

        Example:
        - `[p]timeoutset logchannel #mod-log`
        """
        await self.config.guild(ctx.guild).logchannel.set(channel.id)
        await ctx.message.add_reaction("✅")

    @timeoutset.command(name="report")
    @checks.mod()
    async def timeoutset_report(self, ctx: commands.Context, choice: str):
        """Whether to send a report when a user is added or removed from timeout.

        These reports will be sent in the form of an embed with timeout reason to the configured log channel.
        Set log channel with `[p]timeoutset logchannel`.

        Example:
        - `[p]timeoutset report [choice]`

        Possible choices are:
        - `true` or `yes`: Reports will be sent.
        - `false` or `no`: Reports will not be sent.
        """

        if str.lower(choice) in ["true", "yes"]:
            await self.config.guild(ctx.guild).report.set(True)
            await ctx.message.add_reaction("✅")
        elif str.lower(choice) in ["false", "no"]:
            await self.config.guild(ctx.guild).report.set(False)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.send("Choices: true/yes or false/no")

    @timeoutset.command(name="role")
    @checks.mod()
    async def timeoutset_role(self, ctx: commands.Context, role: discord.Role):
        """Set the timeout role.

        Example:
        - `[p]timeoutset role MyRole`
        """
        await self.config.guild(ctx.guild).timeoutrole.set(role.id)
        await ctx.message.add_reaction("✅")

    @timeoutset.command(name="list")
    @checks.mod()
    async def timeoutset_list(self, ctx: commands.Context):
        """List current settings."""

        log_channel = await self.config.guild(ctx.guild).logchannel()
        report = await self.config.guild(ctx.guild).report()
        timeout_role = ctx.guild.get_role(await self.config.guild(ctx.guild).timeoutrole())

        if log_channel:
            log_channel = f"<#{log_channel}>"
        else:
            log_channel = "Unconfigured"

        if timeout_role is not None:
            timeout_role = timeout_role.name
        else:
            timeout_role = "Unconfigured"

        if report == "":
            report = "Unconfigured"

        # Build embed
        embed = discord.Embed(
            color=(await ctx.embed_colour())
        )
        embed.set_author(
            name="Timeout Cog Settings",
            icon_url=ctx.guild.me.avatar_url
        )
        embed.add_field(
            name="Log Channel",
            value=log_channel,
            inline=True
        )
        embed.add_field(
            name="Send Reports",
            value=report,
            inline=True
        )
        embed.add_field(
            name="Timeout Role",
            value=timeout_role,
            inline=True
        )

        # Send embed
        await ctx.send(embed=embed)

    @commands.command()
    @checks.mod()
    async def timeout(self, ctx: commands.Context, user: discord.Member, *, reason="Unspecified"):
        """Timeouts a user or returns them from timeout if they are currently in timeout.

        See and edit current configuration with `[p]timeoutset`.

        Example:
        - `[p]timeout @user`
        """
        author = ctx.author
        everyone_role = ctx.guild.default_role

        # Find the timeout role in server
        timeout_role_data = await self.config.guild(ctx.guild).timeoutrole()
        timeout_role = ctx.guild.get_role(timeout_role_data)

        if await self.config.guild(ctx.guild).report() and not await self.config.guild(ctx.guild).logchannel():
            await ctx.send("Please set the log channel using `[p]timeoutset logchannel`, or disable reporting.")
            return

        # Notify and stop if command author tries to timeout themselves,
        # or if the bot can't do that.
        if author == user:
            await ctx.send("I cannot let you do that. Self-harm is bad \N{PENSIVE FACE}")
            return

        if ctx.guild.me.top_role <= user.top_role or user == ctx.guild.owner:
            await ctx.send("I cannot do that due to Discord hierarchy rules.")
            return

        # Check if user already in timeout.
        # Remove & restore if so, else timeout.
        if user.roles == [everyone_role, timeout_role]:
            await self.timeout_remove(ctx, user, reason)

        else:
            await self.timeout_add(ctx, user, reason, timeout_role)