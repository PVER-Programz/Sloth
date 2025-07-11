# -*- coding: utf-8 -*-

import interactions
from interactions import Button, ButtonStyle, ActionRow
from interactions.ext.paginators import Paginator
from interactions.api.events import Component
import firebase_admin
from firebase_admin import credentials, firestore, auth
import math
import time
import requests
from random import choice as rand
import urllib.parse
import re
import json



with open("tokens.json", 'r') as f:
	tok_json = json.load(f)
TOKEN = tok_json['bot']
FIREBASE_WEB_API_KEY = tok_json['gservice']

with open("discord_ids.json", 'r') as f:
	ids_json = json.load(f)



bot = interactions.Client(token=TOKEN)
# bot.load_extension("interactions.ext.jurigged")

try:
	cred = credentials.Certificate("gservice.json")
	firebase_admin.initialize_app(cred)
	global db
	db = firestore.client()
except Exception as e:
	print(f"Error initializing Database Admin SDK: {e}")



def sign_in_with_email_and_password(email, password, return_secure_token=False):
	payload = json.dumps({"email": email, "password": password, "return_secure_token": return_secure_token})
	# FIREBASE_WEB_API_KEY = 'NULL'
	rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"

	try:
		r = requests.post(rest_api_url,
						  params={"key": FIREBASE_WEB_API_KEY},
						  data=payload)
		r.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
		return True
	except requests.exceptions.RequestException as e:
		print(f"Error during sign-in request: {e}")
		return False
	except json.JSONDecodeError:
		print("Error decoding JSON response from Firebase.")
		return False



def send_reset_link(EMAIL):
	rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={FIREBASE_WEB_API_KEY}"

	headers = {"Content-Type": "application/json"}
	data = json.dumps({"requestType": "PASSWORD_RESET", "email": EMAIL})

	try:
		response = requests.post(rest_api_url, headers=headers, data=data)
		response.raise_for_status()  # Raise an exception for bad status codes

		print("Password reset email sent successfully!")
		print(response.json()) # You might get some information in the response
		return True
	except requests.exceptions.RequestException as e:
		print(f"Error sending password reset email: {e}")
		if response is not None:
			print(f"Response body: {response.text}")
		return False

def payable(amt, src, dst, nfi, other_dest=False):
	fee = (((src+dst)/10000)*amt)
	price=amt+fee
	if price>200:
		price=price+nfi
	if other_dest:
		price=price+10
	if price<50:
		base=1
		price=price+base
	percent = (amt/price)*100
	print(amt, src, dst, nfi, other_dest)
	print("fee:", fee, 'price:', price, 'percent:', percent)
	return [price, fee, percent]





@interactions.listen()
async def on_ready():
	print(f'{bot.user} has connected to Discord!')
	await bot.get_channel(ids_json['ini_channel']).send(
		f'{bot.user} has connected to Discord!')




@interactions.slash_command(name="profile", sub_cmd_name="delivery_executive", sub_cmd_description="Do you wanna side hustle as a delivery executive ? You get bonus too bruh..")
@interactions.slash_option(
	name="can_deliver",
	description="Select true if you're interested in earning by handling food delivery tasks; else select false.",
	opt_type=interactions.OptionType.BOOLEAN,
	required=True
)
async def cmd_usrid(ctx: interactions.SlashContext, can_deliver: bool):
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(ctx.user.id)
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("😵 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"😵 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>", components=registerBtn)
	else:
		user_doc = db.collection("Users").document(str(ctx.user.id))
		if user_doc.get().exists:
			user_doc.set({"can_deli": can_deliver}, merge=True)
			if can_deliver:
				await ctx.send(f"🍴 Congrats. You are now a food Transporter <:transporter:1384788415874072586>")
			else:
				await ctx.send("Oof.. Ok.. 🫠 ")
		else:
			await ctx.send("ERROR: User not found")



@interactions.slash_command(name="profile", sub_cmd_name="edit", sub_cmd_description="Edit your Profile")
@interactions.slash_option(
	name="name",
	description="Enter name as per VIT id",
	required=False,
	opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
	name="phone_number",
	description="For contact purposes while delivery",
	required=False,
	opt_type=interactions.OptionType.STRING,
	min_length=10,
	max_length=13
)
@interactions.slash_option(
	name='upi_id',
	description="Payment for food via UPI only",
	required=False,
	opt_type=interactions.OptionType.STRING
)
@interactions.slash_option(
	name='hosteller',
	description="Are you a hosteller ?",
	required=False,
	opt_type=interactions.OptionType.BOOLEAN
)
@interactions.slash_option(
	name='gender',
	description="Are you a guy or girl ?",
	required=False,
	opt_type=interactions.OptionType.STRING,
	choices=[
		interactions.SlashCommandChoice(name="Guy", value="Guy"),
		interactions.SlashCommandChoice(name="Girl", value='Girl')
	]
)
async def profile_edit(ctx: interactions.SlashContext, name=None, phone_number=None, upi_id=None, hosteller=None, gender=None):
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(ctx.user.id)
	params = [name, phone_number, upi_id, hosteller, gender]
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("😵 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"😵 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>", components=registerBtn)
	else:
		# try:
			user_doc_ref = db.collection("Users").document(str(ctx.user.id))
			user_dic = user_doc_ref.get().to_dict()
			pc_fill=1
			response = ""
			if name!=None:
				pc_fill+=1
			else:
				name=user_dic['name']
				if name not in user_dic['email']:
					pc_fill+=1
			if phone_number!=None and phone_number not in ["1234567890", "0123456789", "0"*10, "1"*10, "2"*10, "3"*10, "4"*10, "5"*10, "6"*10, "7"*10, "8"*10, "9"*10]:
				pc_fill+=1
			else:
				phone_number = user_dic['phone']
				if phone_number in ["1234567890", "0123456789", "0"*10, "1"*10, "2"*10, "3"*10, "4"*10, "5"*10, "6"*10, "7"*10, "8"*10, "9"*10]:
					response = "📞 Please fill Your Phone Number. It is required by the delivery executives for contact purposes\n"+response
				else:
					pc_fill+=1
			if upi_id!=None and "@" in upi_id and len(upi_id)>4:
				pc_fill+=1
			else:
				upi_id = user_dic['upi']
				if not ("@" in upi_id and len(upi_id)>4):
					response = "📱 Please fill Your UPI id. Delivery bonus will be credited to you via GPay only.\n"+response
				else:
					pc_fill+=1
			if hosteller!=None:
				pc_fill+=1
			else:
				hosteller = user_dic['hosteller']
				if hosteller==None:
					response = "🏠 Are you hosteller or dayscholar bruh ?\n"+response
				else:
					pc_fill+=1
			if gender!=None:
				pc_fill+=1
			else:
				gender = user_dic['gender']
				if gender==None:
					response = "🌚 Not to be nosy but are you he/him or she/her ?\n"+response
				else:
					pc_fill+=1
			pc_score=int((pc_fill/6)*100)
			user_doc_ref.set({'name':name, 'phone':phone_number, 'upi':upi_id, 'hosteller':hosteller, 'gender':gender, 'profile_completion': pc_score}, merge=True)
			#hosteller - stance
			if response!="":
				await ctx.send(response, ephemeral=True)
			if params[0] == None and params[1] == None and params[2] == None and params[3] == None and params[4] == None:
				await ctx.send("Use </profile page:1385296092232552570> to view Profile")
			else:
				await ctx.send(f"{ctx.user.mention} ✅ Your profile has been updated successfully!")
		# except Exception as e:
		# 	await ctx.send(f"❌ An error occurred while updating your profile")

@interactions.slash_command(name="profile", sub_cmd_name="page", sub_cmd_description="View your Profile")
async def profile_view(ctx: interactions.SlashContext):
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(ctx.user.id)
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("😵 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"😵 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>", components=registerBtn)
		return
	else:
		user_doc_ref = db.collection("Users").document(str(ctx.user.id))
		user_doc = user_doc_ref.get()
		user_data = user_doc.to_dict()
	embed = interactions.Embed(
		title="Your Profile Page",
		description="Use </profile edit:1385296092232552570> to edit profile",
		color=0xFAD35C,
	)

	embed.add_field(
		name="Name",
		value=user_data['name'],
		inline=False,
	)
	embed.add_field(
		name="Email",
		value=user_data['email'],
		inline=False,
	)
	embed.add_field(
		name="Phone number",
		value=user_data['phone'],
		inline=True,
	)
	embed.add_field(
		name="UPI ID",
		value=user_data['upi'],
		inline=True,
	)
	embed.add_field(
		name="Cart Items",
		value=str("Use </cart:1385296092232552571> to view your cart"),
		inline=False,
	)
	embed.add_field(
		name="Stance",
		value="Hosteller" if user_data['hosteller'] else "None" if user_data['hosteller']==None else "Dayscholar",
		inline=True,
	)
	embed.add_field(
		name="Selfhood",
		value="Guy" if user_data['gender'] else "None" if user_data['gender']==None else "Girl",
		inline=True,
	)
	embed.add_field(
		name="Can Deliver",
		value=str(user_data['can_deli']),
		inline=True,
	)
	embed.add_field(
		name="Profile Completion",
		value=f"{user_data['profile_completion']}%",
		inline=True,
	)
	embed.add_field(
		name="UPI QR",
		value="Your UPI QR:",
		inline=False,
	)
	url_string = user_data['upi']
	encoded_path = urllib.parse.quote(url_string, safe='')
	redirect_url = f"https://pver-programz.github.io/url-redirector/?url={encoded_path}"
	if "@" in user_data['upi'] and " " not in user_data['upi'].strip():
		embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=225x225&data=upi://pay?pa={url_string}")
	else:
		embed.set_image(url=f"https://placehold.co/600x300/FF0000/FFFFFF.png?text=UPI_not_set")
	await ctx.send(embed=embed, ephemeral=True)

registerBtn = Button(
	custom_id="register_btn",
	style=ButtonStyle.PRIMARY,
	label="Register",
)

connectBtn = Button(
	custom_id="connect_btn",
	style=ButtonStyle.GREEN,
	label="Connect",
)

gmailBtn = Button(
	url="https://mail.google.com",
	style=ButtonStyle.URL,
	label="Open gmail",
)

@interactions.slash_command(name="register", description="Register for first time user")
@interactions.slash_option(
	name="vit_email",
	description="Enter your VIT Email (@vitstudent.ac.in)",
	required=True,
	opt_type=interactions.OptionType.STRING,
	min_length=20
)
async def register(ctx: interactions.SlashContext, vit_email: str):
	email = vit_email
	await ctx.defer()
	if email.strip().endswith("@vitstudent.ac.in"):
		users_collection = db.collection("Users")
		try:
			user = auth.get_user_by_email(email)
			query = users_collection.where("email", "==", email)
			res=query.stream()
			disids = " "
			id_count=0
			for x in res:
				disids=disids+f"<@{x.id}>"
				id_count=id_count+1
			if id_count>0:
				await ctx.send(f"User with email `{email[:4]}****@vitstudent.ac.in` already exists. and registered to {disids}")
			else:
				if send_reset_link(email):
					await ctx.send("Check your email for a password reset link. Set your password and then Use </connect:1385296092232552574> to connect your discord to Sloth App.\n`Check Spam folder too`", components=[gmailBtn, connectBtn])
				else:
					await ctx.send("Registration ERROR: Unable to send verification mail.")
				# link = auth.generate_password_reset_link(email)
				# await ctx.send(f"user {user.uid} \n link {link}", components=[gmailBtn, connectBtn])
		except auth.UserNotFoundError:
			user = auth.create_user(email=email,password=email[::-1])
			if send_reset_link(email):
				await ctx.send("Check your email for a password reset link. Use </connect:1385296092232552574> to connect your discord to Sloth App.\n`Check Spam folder too`", components=[gmailBtn, connectBtn])
			else:
				await ctx.send("Registration ERROR: Unable to send verification mail.")
		except:
			await ctx.send("ERROR Occured. Please Try Again")
	else:
		await ctx.send("Use VIT student email.")

@interactions.component_callback("register_btn")
async def component_register(ctx: interactions.ComponentContext):
	reg_modal = interactions.Modal(
		interactions.ShortText(label="Enter your VIT Email", custom_id="reg_short_text", min_length=20),
		title="Register User",
		custom_id="reg_modal",
	)
	await ctx.send_modal(modal=reg_modal)


@interactions.modal_callback("reg_modal")
async def reg_modal_response(ctx: interactions.ModalContext, reg_short_text: str):
	email = reg_short_text
	print('here')
	await ctx.defer()
	if email.strip().endswith("@vitstudent.ac.in"):
		users_collection = db.collection("Users")
		try:
			user = auth.get_user_by_email(email)
			query = users_collection.where("email", "==", email)
			res=query.stream()
			disids = " "
			id_count=0
			for x in res:
				disids=disids+f"<@{x.id}>"
				id_count=id_count+1
			if id_count>0:
				await ctx.send(f"User with email `{email[:4]}****@vitstudent.ac.in` already exists. and registered to {disids}")
			else:
				if send_reset_link(email):
					await ctx.send("Check your email for a password reset link. Set your password and then Use </connect:1385296092232552574> to connect your discord to Sloth App.", components=[gmailBtn, connectBtn])
				else:
					await ctx.send("Registration ERROR: Unable to send verification mail.")
				# link = auth.generate_password_reset_link(email)
				# await ctx.send(f"user {user.uid} \n link {link}", components=[gmailBtn, connectBtn])
		except auth.UserNotFoundError:
			user = auth.create_user(email=email,password=email[::-1])
			if send_reset_link(email):
				await ctx.send("Check your email for a password reset link. Use </connect:1385296092232552574> to connect your discord to Sloth App.", components=[gmailBtn, connectBtn])
			else:
				await ctx.send("Registration ERROR: Unable to send verification mail.")
		except:
			await ctx.send("ERROR Occured. Please Try Again")
	else:
		await ctx.send("Use VIT student email.")




@interactions.slash_command(name="connect", description="Verifies your discord so that you can place orders")
async def connect(ctx: interactions.SlashContext):
	con_modal = interactions.Modal(
		interactions.ShortText(label="Enter your VIT Email", custom_id="con_short_text", min_length=20),
		interactions.ShortText(label="Enter the password", custom_id="pwd_text", placeholder="Check your mail for password reset link.", min_length=6),
		title="Register User",
		custom_id="con_modal",
	)

	await ctx.send_modal(modal=con_modal)
	# modal_ctx: interactions.ModalContext = await ctx.bot.wait_for_modal(con_modal)

@interactions.component_callback("connect_btn")
async def component_connect(ctx: interactions.ComponentContext):
	con_modal = interactions.Modal(
		interactions.ShortText(label="Enter your VIT Email", custom_id="con_short_text", min_length=20),
		interactions.ShortText(label="Enter the password", custom_id="pwd_text", placeholder="Check your mail for password reset link.", min_length=6),
		title="Register User",
		custom_id="con_modal",
	)
	await ctx.send_modal(modal=con_modal)

@interactions.modal_callback("con_modal")
async def con_modal_response(modal_ctx: interactions.ModalContext, con_short_text: str, pwd_text: str):
	email = con_short_text
	password = pwd_text
	await modal_ctx.defer()
	users_collection = db.collection("Users")
	if users_collection.document(str(modal_ctx.user.id)).get().exists:
		await modal_ctx.send("🤡 User already connected")
	else:
		if email.strip().endswith("@vitstudent.ac.in"):
			try:
				trigger_except_block = auth.get_user_by_email(email)
				if sign_in_with_email_and_password(email, password):
					dis_uid = modal_ctx.user.id
					guild = await bot.fetch_guild(ids_json['server_id'])
					member = guild.get_member(dis_uid)
					user_data = {"email": email, "username": modal_ctx.user.username, "in_deli": False, "can_deli": True, 'cart':{}, 'cart_res':None,
								"name": email[:email.index('@')], "phone": '0000000000', "upi": "not_set", "profile_completion": int((1/6)*100),
								"gender": None, "hosteller": None}
					users_collection.document(str(modal_ctx.user.id)).set(user_data)
					await member.add_role(ids_json['veri_role'])
					await modal_ctx.send(f"<@{dis_uid}> Just got Verified 🏆\n\nUse </profile page:1385296092232552570> to view your profile.")
				else:
					await modal_ctx.send("Unable to Verify. If this Email is registered, check mail for password reset link. Set your password and then retry.")
			except auth.UserNotFoundError:
				await modal_ctx.send("Invalid Email: This Email is not registered. Use </register:1385296092232552573> to register", components=registerBtn)
		else:
			await modal_ctx.send("Use VIT student email.")




@interactions.slash_command(name="menu", description="View Available dishes")
async def menu_view(ctx: interactions.SlashContext):
	restraunts = db.collection("Menu").stream()
	res_data = {}
	for res in restraunts:
		res_data[res.id] = res.to_dict()
	# lis25 = split_dict_into_chunks(res_data[x])
	embed_array=[]
	for x in res_data:
		embed = interactions.Embed(
			title=x,
			description="Clcik </cart:1385296092232552571> to add items to cart",
			color=0xFAD35C,
		)
		for z in res_data[x]:
			embed.add_field(
				name=f'{"✅" if res_data[x][z][1] else "🔴"} {z}',
				# name=f'{z} [{res_data[x][z][2]}] ',
				value=f"₹{res_data[x][z][0]}",
				inline=True
				)
		embed_array.append(embed)
	paginator = Paginator.create_from_embeds(bot, *embed_array)
	paginator.show_select_menu = True
	await paginator.send(ctx)


@interactions.slash_command(name="order", description="Ordering Food ?")
async def order_command(ctx: interactions.SlashContext):
	embed = interactions.Embed(
		title="Order Food",
		description="Verify </cart:1385296092232552571> before you buy.",
		color=0x00FF00
	)
	await ctx.send(embeds=embed)



@interactions.slash_command(name="example_embed", description="Responds with an example embed message.",
)
async def example_embed_command(ctx: interactions.SlashContext):
	embed = interactions.Embed(
		title="✨ Example Embed Message ✨",
		description="This is a demonstration of various fields available in a Discord embed.",
		color=0xFAD35C,
		timestamp=123457,
		url="https://discord.com/",
	)

	embed.set_author(
		name="Embed Bot",
		url="https://example.com/bot-profile",
		icon_url="https://placehold.co/64x64/FF5733/FFFFFF.png.png?text=BOT",
	)

	embed.set_thumbnail(url="https://placehold.co/128x128/33FF57/000000.png?text=Thumb")

	embed.add_field(
		name="Field 1: Inline True",
		value="This field is set to `inline=True`.",
		inline=True,
	)
	embed.add_field(
		name="Field 2: Inline True",
		value="This field is also `inline=True`, so it appears next to Field 1 if space allows.",
		inline=True,
	)
	embed.add_field(
		name="Field 3: Inline False",
		value="This field is set to `inline=False`, so it will always start on a new line.",
		inline=False,
	)
	embed.add_field(
		name="Longer Field Example",
		value="""This is an example of a field with a longer value. You can include
		multiple lines of text here. Markdown like **bold**, *italics*,
		`code snippets`, and [links](https://www.google.com) also work!""",
		inline=False,
	)

	embed.set_image(url="https://placehold.co/600x300/DB3498/FFFFFF.png?text=Main+Image")

	embed.set_footer(
		text="This is an example footer text.",
		icon_url="https://placehold.co/32x32/9B59B6/FFFFFF.png?text=FOOT",
	)

	await ctx.send(f"Added: {embed.timestamp}", embed=embed)


@interactions.slash_command(name="cart", description="View your Cart details")
async def cart_view(ctx: interactions.SlashContext):
	await ctx.defer(ephemeral=True)
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(ctx.user.id)
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("😵 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"😵 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>", components=registerBtn)
	else:
		restraunts = db.collection("Menu").stream()
		res_data = {}
		for res in restraunts:
			res_data[res.id] = res.to_dict()

		user_doc_ref = db.collection("Users").document(str(ctx.user.id))
		user_doc = user_doc_ref.get()
		if user_doc.exists:
			user_data = user_doc.to_dict()
			try:
				cart = user_data['cart']
				cart_res = user_data['cart_res']
			except KeyError:
				cart = {}
				cart_res=None
		else:
			cart = {}
			cart_res=None
		menu_col = db.collection("Menu")
		embed = interactions.Embed(
		title="Cart View",
		# description=f"Cart Size: {len(cart)}",
		color=0xFAD35C,
		)

		embed.set_author(
		name=ctx.user.username,
		icon_url=ctx.user.avatar.url,
		)

		if len(cart)!=0:
			embed.set_thumbnail(url=f"https://placehold.co/128x128/FAD35C/000000.png?text={cart_res}")

		tot_size = 0
		tot_cost=0
		if cart_res!=None and len(cart)!=0:
			dishes_dic = menu_col.document(cart_res).get().to_dict()
			for x in cart:
				dish_data=dishes_dic[x]
				avail = "✅" if dish_data[1] else "🔴"
				embed.add_field(
					name=f"{x} [{cart[x]}]",
					value=f"""Cost: ₹{dish_data[0]} - Availablity: {avail}""",
					inline=False,
				)
				tot_cost+=dish_data[0]*cart[x]
				tot_size+=cart[x]
		else:
			print("Empty Cart")
		embed.description = f"{tot_size} items currently in cart"
		embed.set_footer(text=f"Total Cost: ₹{tot_cost}")

		user_doc = db.collection("Users").document(str(ctx.user.id))
		try:
			sel_res_placehold = user_data['cart_res']
		except KeyError:
			sel_res_placehold = list(res_data.keys())[-1]
		user_doc.set({'selected_dish':None, 'selected_count': 1, 'selected_res': sel_res_placehold, 'cart_total': tot_cost}, merge=True)
		buy_button = Button(style=ButtonStyle.GREEN, label="Buy", custom_id="buy_button")
		add2cart_button = Button(style=ButtonStyle.PRIMARY, label="Add to cart", custom_id="a2c_button", emoji="🛒")
		remove_from_cart_button = Button(style=ButtonStyle.SECONDARY, label="Remove from cart", custom_id="r2c_button", emoji="🛒")
		clear_button = Button(style=ButtonStyle.DANGER, label="Clear Cart", custom_id="clear_button")
		actRow0 = ActionRow(buy_button, clear_button)
		actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder=f"Choose to Buy from ?", custom_id="res_men", min_values=1, max_values=1))
		try:
			actRow2 = ActionRow(interactions.StringSelectMenu(*user_data['selactable_dislis'], placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
			# actRow2 = ActionRow(interactions.StringSelectMenu(*user_data['selactable_dislis'], placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=len(user_data['selactable_dislis'])))
		except KeyError:
			actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
			# actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=len(list(res_data[list(res_data.keys())[-1]].keys()))))
		actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder="How many to buy ?", custom_id="dish_cou", min_values=1, max_values=1))
		actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
		# global_users[ctx.user.id]['comp'] = [actRow0, actRow1, actRow2, actRow3, actRow4]
		message = await ctx.send("Use </menu:1385296092232552569> to view available dishes to order", embed=embed, components=[actRow0, actRow1, actRow2, actRow3, actRow4], ephemeral=True)



@interactions.component_callback("res_men")
async def res_men_callback(ctx):
	await ctx.defer(edit_origin=True)
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values[0]
	dislis = list(db.collection("Menu").document(choice).get().to_dict().keys())
	user_doc.set({'selactable_dislis':dislis}, merge=True)
	buy_button = Button(style=ButtonStyle.GREEN, label="Buy", custom_id="buy_button")
	add2cart_button = Button(style=ButtonStyle.PRIMARY, label="Add to cart", custom_id="a2c_button", emoji="🛒")
	remove_from_cart_button = Button(style=ButtonStyle.SECONDARY, label="Remove from cart", custom_id="r2c_button", emoji="🛒")
	clear_button = Button(style=ButtonStyle.DANGER, label="Clear Cart", custom_id="clear_button")
	res_data = {}
	for res in db.collection("Menu").stream():
		res_data[res.id] = res.to_dict()
	actRow0 = ActionRow(buy_button, clear_button)
	actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder=choice, custom_id="res_men", min_values=1, max_values=1))
	actRow2 = ActionRow(interactions.StringSelectMenu(*dislis, placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
	# actRow2 = ActionRow(interactions.StringSelectMenu(*dislis, placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=len(dislis)))
	actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder="How many to buy ?", custom_id="dish_cou", min_values=1, max_values=1))
	actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
	components=[actRow0, actRow1, actRow2, actRow3, actRow4]
	user_doc.set({'selected_res':f'{choice}', 'selected_dish':None,'selected_count':None}, merge=True)
	await ctx.edit_origin(content = f"Selected Restraunt: {choice}", components=components)

@interactions.component_callback("dish_men")
async def dish_men_callback(ctx):
	await ctx.defer(edit_origin=True)
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values[0]
	buy_button = Button(style=ButtonStyle.GREEN, label="Buy", custom_id="buy_button")
	add2cart_button = Button(style=ButtonStyle.PRIMARY, label="Add to cart", custom_id="a2c_button", emoji="🛒")
	remove_from_cart_button = Button(style=ButtonStyle.SECONDARY, label="Remove from cart", custom_id="r2c_button", emoji="🛒")
	clear_button = Button(style=ButtonStyle.DANGER, label="Clear Cart", custom_id="clear_button")
	res_data = {}
	for res in db.collection("Menu").stream():
		res_data[res.id] = res.to_dict()
	user_dic = user_doc.get().to_dict()
	actRow0 = ActionRow(buy_button, clear_button)
	try:
		actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder=user_dic['selected_res'], custom_id="res_men", min_values=1, max_values=1))
	except KeyError:
		actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder="Choose to Buy from ?", custom_id="res_men", min_values=1, max_values=1))
	try:
		actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=choice, custom_id="dish_men", min_values=1, max_values=1))
	except KeyError:
		actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
	actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder="How many to buy ?", custom_id="dish_cou", min_values=1, max_values=1))
	actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
	components=[actRow0, actRow1, actRow2, actRow3, actRow4]
	user_doc.set({'selected_dish':choice, 'selected_count':None}, merge=True)
	await ctx.edit_origin(content=f"Selected Dishes: {choice}", components=components)

@interactions.component_callback("dish_cou")
async def dish_cou_callback(ctx):
	await ctx.defer(edit_origin=True)
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values[0]
	buy_button = Button(style=ButtonStyle.GREEN, label="Buy", custom_id="buy_button")
	add2cart_button = Button(style=ButtonStyle.PRIMARY, label="Add to cart", custom_id="a2c_button", emoji="🛒")
	remove_from_cart_button = Button(style=ButtonStyle.SECONDARY, label="Remove from cart", custom_id="r2c_button", emoji="🛒")
	clear_button = Button(style=ButtonStyle.DANGER, label="Clear Cart", custom_id="clear_button")
	res_data = {}
	for res in db.collection("Menu").stream():
		res_data[res.id] = res.to_dict()
	user_dic = user_doc.get().to_dict()
	actRow0 = ActionRow(buy_button, clear_button)
	try:
		actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder=user_dic['selected_res'], custom_id="res_men", min_values=1, max_values=1))
	except KeyError:
		actRow1 = ActionRow(interactions.StringSelectMenu(*list(res_data.keys()), placeholder="Choose to Buy from ?", custom_id="res_men", min_values=1, max_values=1))
	try:
		actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=user_dic['selected_dish'], custom_id="dish_men", min_values=1, max_values=1))
	except KeyError:
		actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
	actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder=f"{choice}", custom_id="dish_cou", min_values=1, max_values=1))
	actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
	components=[actRow0, actRow1, actRow2, actRow3, actRow4]
	user_doc.set({'selected_count':int(choice)}, merge=True)
	await ctx.edit_origin(content=f"Selected Dishes will be added/removed {choice} times to your cart", components=components)

@interactions.component_callback("a2c_button")
async def a2c_callback(ctx):
	try:
		await ctx.defer(edit_origin=True)
		user_doc = db.collection("Users").document(str(ctx.user.id))
		user_dic = user_doc.get().to_dict()
		res_change=False
		if 'selected_dish' in user_dic and user_dic['selected_dish'] is not None:
			if user_dic['cart_res'] != user_dic['selected_res']:
				user_doc.set({'cart':{}}, merge=True)
				user_dic['cart']={}
				user_dic['cart_res']=user_dic['selected_res']
				res_change=True
				print('restraunt changed', 'cart:', user_dic['cart'])
			try:
				if user_dic['selected_count']!=None and user_dic['selected_dish'] in user_dic['cart']:
					user_dic['cart'][user_dic['selected_dish']] += user_dic['selected_count']
				elif user_dic['selected_count']==None and user_dic['selected_dish'] in user_dic['cart']:	
					user_dic['cart'][user_dic['selected_dish']] += 1
				elif user_dic['selected_count']!=None and user_dic['selected_dish'] not in user_dic['cart']:
					user_dic['cart'][user_dic['selected_dish']] = user_dic['selected_count']
				elif user_dic['selected_count']==None and user_dic['selected_dish'] not in user_dic['cart']:	
					user_dic['cart'][user_dic['selected_dish']] = 1
			except KeyError as e:
				print(f"key error {e}")
			###############
			cart=user_dic['cart']
			cart_res=user_dic['selected_res']
			menu_col = db.collection("Menu")
			embed = interactions.Embed(title="Cart View", 
				# description=f"{len(cart)} items currently in cart",
				color=0xFAD35C)
			embed.set_author(name=ctx.user.username, icon_url=ctx.user.avatar.url)
			if len(cart)!=0:
				embed.set_thumbnail(url=f"https://placehold.co/128x128/FAD35C/000000.png?text={cart_res}") ########## A2C
			tot_cost=0
			tot_size=0
			dish_dic = menu_col.document(cart_res).get().to_dict()
			for x in cart:
				dish_data = dish_dic[x]
				avail = "✅" if dish_data[1] else "🔴"
				embed.add_field(
					name=f"{x} [{cart[x]}]",
					value=f"""Cost: ₹{dish_data[0]} - Availablity: {avail}""",
					inline=False,
				)
				tot_cost+=dish_data[0]*cart[x]
				tot_size+=cart[x]
			embed.description = f"{tot_size} items currently in cart"
			embed.set_footer(text=f"Total Cost: ₹{tot_cost}")
			user_doc.set({'cart':user_dic['cart'], 'cart_res':user_dic['cart_res'], 'cart_total': tot_cost}, merge=True)
			if res_change:
				await ctx.edit_origin(content =f"Selected Restraunt is changed to {user_dic['selected_res']}. Cart Cleared.", embed=embed)
			else:
				await ctx.edit_origin(content="Use </menu:1385296092232552569> to view available dishes to order", embed=embed)	
		else:
			await ctx.channel.send(f"<@{ctx.user.id}>\n 💢 Please select Product to add to cart.", ephemeral=True, delete_after=2)
	except Exception as e:
		print(type(e), e)
		await ctx.send("Error Occured.")

@interactions.component_callback("r2c_button")
async def r2c_callback(ctx):
	user_doc = db.collection("Users").document(str(ctx.user.id))
	user_dic = user_doc.get().to_dict()
	if user_dic['selected_count']==None:
		user_dic['selected_count']=1
	try:
		user_dic['cart'][user_dic['selected_dish']] -= user_dic['selected_count']
		if user_dic['cart'][user_dic['selected_dish']] <= 0:
			user_dic['cart'][user_dic['selected_dish']] = firestore.DELETE_FIELD
	except KeyError as e:
		await ctx.send(f"{user_dic['selected_dish']} is not in cart to remove", delete_after=2, ephemeral=True)
		return
	cart=user_dic['cart']
	cart_res=user_dic['selected_res']
	menu_col = db.collection("Menu")
	embed = interactions.Embed(title="Cart View", description=f"{len(cart)} items currently in cart", color=0xFAD35C)
	embed.set_author(name=ctx.user.username, icon_url=ctx.user.avatar.url)
	if len(cart)!=0:
		embed.set_thumbnail(url=f"https://placehold.co/128x128/FAD35C/000000.png?text={cart_res}") ########## A2C
	tot_cost=0
	tot_size=0
	dish_res = menu_col.document(cart_res).get().to_dict()
	for x in cart:
		try:
			dish_data=dish_res[x]
			avail = "✅" if dish_data[1] else "🔴"
			embed.add_field(
				name=f"{x} [{int(cart[x])}]",
				value=f"""Cost: ₹{dish_data[0]} - Availablity: {avail}""",
				inline=False,
			)
			tot_cost+=dish_data[0]*cart[x]
			tot_size+=cart[x]
		except Exception as e:
			print(type(e), e)
	embed.description = f"{tot_size} items currently in cart"
	user_doc.set({'cart':user_dic['cart'], 'cart_total':tot_cost}, merge=True)
	embed.set_footer(text=f"Total Cost: ₹{tot_cost}")
	await ctx.edit_origin(content="Use </menu:1385296092232552569> to view available dishes to order", embed=embed)	


@interactions.component_callback("buy_button")
async def buy_button_callback(ctx: interactions.ComponentContext):
	await ctx.defer(ephemeral=True)
	dests = db.collection('Distance').document('destination').get().to_dict()
	dest_list = sorted(list(dests.keys())) + ["Others"]
	drop_men = interactions.StringSelectMenu(*dest_list, placeholder='Select Drop location', custom_id="dest_men", min_values=1, max_values=1)
	await ctx.send(content="Select Drop off location", components=drop_men, ephemeral=True)

@interactions.component_callback("dest_men")
async def dest_men_callback(ctx):
	if ctx.values[0] != "Others":
		loc = ctx.values[0]
		# await ctx.message.edit(content='Thank You', components=[])
	else:
		loc=None
		# await ctx.message.edit(content='Custom drop locations will be charged 10rs delivery fee', components=[])
	ph = rand(["It's my Lunch. Bring ASAP Please.", "Drop by 2 PM.", "Don't forget ketchup", "Enjoy extra tips", "Bring 2 More Spoons please"])
	if loc!=None:
		ord_modal = interactions.Modal(
			interactions.ShortText(label="Drop Point Room no.", custom_id="drop_text", required=True, placeholder="Example: 708"),
			interactions.ShortText(label="Drop Location", custom_id="drop_dest", required=True, value=loc),
			interactions.ParagraphText(label="Delivery Instructions", custom_id="inst_text", placeholder=f"Eg: {ph}", required=False),
			title=f"Final details for Order",
			custom_id="ord_modal",
		)
	else:
		ord_modal = interactions.Modal(
			interactions.ShortText(label="Drop Point Room no.", custom_id="drop_text", required=False, placeholder="Example: AB-1 708"),
			interactions.ShortText(label="Drop Location", custom_id="drop_dest", required=True, placeholder="Custom drop location will be charged extra", value=" "),
			interactions.ParagraphText(label="Delivery Instructions", custom_id="inst_text", placeholder=f"Eg: {ph}", required=False),
			title=f"Final details for Order",
			custom_id="ord_modal",
		)
	user_data = db.collection('Users').document(str(ctx.user.id)).get().to_dict()
	if user_data['cart'] == {}:
		await ctx.send(f"{ctx.user.mention}\n🤕 Your Cart is empty")
	elif user_data['profile_completion'] > 90:
		await ctx.send_modal(modal=ord_modal)
	else:
		await ctx.send(f"{ctx.user.mention}\n📉 Your profile is not Complete. Complete Your profile using </profile edit:1385296092232552570> to place order.\nCurrent Profile Completion: **{user_data['profile_completion']}**%")


@interactions.modal_callback("ord_modal")
async def ord_modal_answer(ctx: interactions.ModalContext,  drop_text: str, inst_text: str, drop_dest=None):
	await ctx.defer()
	ord_no = str(int(time.time()))
	order_doc = db.collection("orders").document(ord_no)
	try:
		users_ref = db.collection('Users')
		dist_dict = db.collection('Distance').document('destination').get().to_dict()
		src_dict = db.collection('Distance').document('source').get().to_dict()
		query = users_ref.where('can_deli', '==', True).stream()
		user_data = users_ref.document(str(ctx.user.id)).get().to_dict()
		if drop_dest in dist_dict:
			drop_params = [src_dict[user_data['cart_res']], dist_dict[drop_dest], False]
			topay = payable(int(user_data['cart_total']), src_dict[user_data['cart_res']], dist_dict[drop_dest], sum(user_data['cart'].values()))
		else:
			drop_params = [src_dict[user_data['cart_res']], 500, True]
			topay = payable(int(user_data['cart_total']), src_dict[user_data['cart_res']], 500, sum(user_data['cart'].values()), True)
		requested_users_id_msgs = {}
		acc_button = Button(style=ButtonStyle.GREEN, label="Accept", custom_id="acc_button")
		viewDet_button = Button(style=ButtonStyle.SECONDARY, label="View Details", custom_id="viewdetails_button")
		dec_button = Button(style=ButtonStyle.DANGER, label="Decline", custom_id="dec_button")
		for doc in query:
			if str(doc.id) != str(ctx.user.id):
				guild = await ctx.bot.fetch_guild(ids_json['server_id'])
				guild_member = await guild.fetch_member(int(doc.id))
				if guild_member!=None:
					member_dm = await guild_member.fetch_dm()
					add_text = f"{ctx.user.mention} needs your help\nOrder No. *[{ord_no}]*\nDrop-point: **{drop_dest} {drop_text}**\n{inst_text}"
					add_text=add_text+f"\nEstimated delivery bonus: **{topay[2]:.2f}% - {topay[2]+10:.2f}%** of order value"
					dm_message = await member_dm.send(f"{add_text}\n**Are you willing to deliver ?**", components=[acc_button, dec_button])
					requested_users_id_msgs[str(doc.id)]=str(dm_message.id)
					print("DMed:", guild_member.tag)
				else:
					print("Not member:", guild_member.tag)
		update_button = Button(style=ButtonStyle.PRIMARY, label="Order Status", custom_id="upd_button")
		canc_button = Button(style=ButtonStyle.DANGER, label="Cancel", custom_id="canc_button")
		userDmRow = ActionRow(update_button, canc_button)
		user_dm = await ctx.user.fetch_dm()
		cart_text=''
		for x in user_data['cart']:
			cart_text=f"{cart_text}{x} - {user_data['cart'][x]}\n"
		embed = interactions.Embed(description=cart_text, color=0xFAD35C)
		embed.add_field(name=f"Net Payable Amount", value=f"₹ ~~{topay[0]+10:.2f}~~  ₹{topay[0]:.2f}", inline=False)
		user_dm_msg = await user_dm.send(f"Order No. *[{ord_no}]* \nYou have placed order for\n", embed=embed, components=[userDmRow])
		ord_chan_msg = await bot.get_channel(ids_json['order_channel']).send(f"{ctx.user.mention} Order No. *[{ord_no}]* \nDelivery to **{drop_dest} {drop_text}**\n{inst_text}", components=[acc_button, viewDet_button])
		ord_details={'customer':str(ctx.user.id), 'drop':[drop_dest,drop_text], 'instruction':inst_text, 'requestees':requested_users_id_msgs, 
					'user_dm_msgid': str(user_dm_msg.id), 'ord_chan_msgid':str(ord_chan_msg.id), 'status': 'open', 'cart':user_data['cart'],
					'cart_total': user_data['cart_total'], 'cart_res':user_data['cart_res'], 'topay':topay[0], 'deliverer': None,
					'half_paid_1': [False, False], 'half_paid_2': [False, False], 'drop_params': drop_params}
		# print("\nOrder details db write:\n", ord_details, "\n")
		order_doc.set(ord_details, merge=True)
		await ctx.send(f"{ctx.user.mention} Placed an Order \nFetching the Perfect person for you. Please wait until someone accepts to deliver your order.")
	except Exception as e:
		print(type(e), e)
		await ctx.send(f"ERROR Occured")

@interactions.component_callback("clear_button")
async def clear_button_callback(ctx: interactions.ComponentContext):
	try:
		user_doc = db.collection("Users").document(str(ctx.user.id)).set({'cart':{}}, merge=True)
		new_embed = interactions.Embed(
			title="Cart View",
			description=f"Cart Size: 0",
			color=0xFAD35C,
			)

		new_embed.set_author(
			name=ctx.user.username,
			icon_url=ctx.user.avatar.url,
			)

		new_embed.set_footer(text=f"Total Cost: ₹0")

		await ctx.message.edit(embeds=new_embed, components=[])
	except:
		await ctx.send("ERROR: Unable to Clear Cart")

canceledBtn = Button(
	custom_id="cancelled_btn",
	style=ButtonStyle.SECONDARY,
	label="Cancelled",
	disabled=True,
	emoji="❌"
)

acceptedBtn = Button(
	custom_id="accepted_btn",
	style=ButtonStyle.SECONDARY,
	label="Accepted",
	disabled=True,
	emoji="👍"
)


declinedBtn = Button(
	custom_id="cancelled_btn",
	style=ButtonStyle.SECONDARY,
	label="Declined",
	disabled=True,
	emoji="🗑️"
)


@interactions.component_callback("acc_button")
async def acc_button_callback(ctx: interactions.ComponentContext):
	await ctx.defer(ephemeral=True)
	user_dic = db.collection('Users').document(str(ctx.user.id)).get().to_dict()
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(ctx.user.id)
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("😵 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"😵 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>", components=registerBtn)
		return
	else:
		pc=user_dic['profile_completion']
		if pc<90:
			await ctx.send(f"{ctx.user.mention}\n📉 Your profile is not Complete. Complete Your profile using </profile edit:1385296092232552570> to accept orders.\nCurrent Profile Completion: **{pc}**%", delete_after=5)
			return
	cont=ctx.message.content
	if str(cont[cont.index('<@')+2:cont.index('>')])!=str(ctx.user.id):
		ord_no = cont[cont.index('[')+1:cont.index(']')]
		doc_ref = db.collection('orders').document(ord_no)
		doc_data = doc_ref.get().to_dict()
		await ctx.message.edit(components=acceptedBtn)
		if ctx.guild == None:
			await bot.get_channel(ids_json['order_channel']).get_message(doc_data['ord_chan_msgid']).delete() # Acc in DM
			acc_inChan = False
		else:
			acc_inChan = True # Acc in channel
		await ctx.send("🚀 Order Accepted", ephemeral=True, delete_after=2)

		guild = await ctx.bot.fetch_guild(ids_json['server_id'])
		for requestee_id in doc_data['requestees']:
			guild_member = await guild.fetch_member(requestee_id)
			if guild_member!=None:
				member_dm = await guild_member.fetch_dm()
				if requestee_id!=str(ctx.user.id):
					await member_dm.get_message(doc_data['requestees'][requestee_id]).delete()
				elif acc_inChan:
					await member_dm.get_message(doc_data['requestees'][requestee_id]).edit(components=acceptedBtn)
		deliverer = str(ctx.user.id)
		adv_amt=int(doc_data['topay']/2)+1
		url_string = f"upi://pay?pa={user_dic['upi']}&am={adv_amt}&tn=Order{ord_no}_adv&cu=INR"
		print("upi url: ", url_string)
		encoded_path = urllib.parse.quote(url_string, safe='')
		redirect_url = f"https://pver-programz.github.io/url-redirector/?url={encoded_path}"
		embed = interactions.Embed(
				title="Payment Screen",
				description="Half of the payment must be done in advance",
				color=0xFAD35C,
				url=redirect_url,
			)
		embed.add_field(
			name="Advance amount",
			value=f"₹ {adv_amt}",
			inline=True,
			)
		embed.add_field(
			name="Payment QR",
			value=f"Pay via UPI only",
			inline=True,
			)
		embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=225x225&data={encoded_path}")
		payBtn = Button(url=redirect_url, style=ButtonStyle.URL, label="Pay")
		veriBtn = Button(style=ButtonStyle.SECONDARY, label="Verify Payment", custom_id=f'veriBtn_{ord_no}_1')
		guild_member = await guild.fetch_member(deliverer)
		if guild_member!=None:
			deliverer_dm = await guild_member.fetch_dm()
			await deliverer_dm.send(f"Order no. *[{ord_no}]*\nThank you for accepting. Your Advance Payment will be credited to you via UPI shortly.")
		doc_ref.set({'deliverer': deliverer, 'status':"due"}, merge=True)
		guild_member = await guild.fetch_member(doc_data['customer'])
		if guild_member!=None:
			member_dm = await guild_member.fetch_dm()
			await member_dm.send(f"Your order *[{ord_no}]* has been accepted by <@{deliverer}>. Proceed with payment to continue.\nPay the amount and click verify.", embed=embed, components=[payBtn, veriBtn])
	else:
		await ctx.send("Bro you dumb ? You cannot accept your own order..!!", ephemeral=True)



veriBtn_regex_pattern = re.compile(r"veriBtn_([0-9]+)_([0-9]+)")
@interactions.component_callback(veriBtn_regex_pattern)
async def veriBtn_callback(ctx):
	match = veriBtn_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
		pay_index = match.group(2)
	print('veri button', ord_no, 'pay_index: ', pay_index)
	yesBtn = Button(style=ButtonStyle.GREEN, label="Confirm", custom_id=f'yesBtn_{ord_no}_{pay_index}')
	noBtn = Button(style=ButtonStyle.DANGER, label="Cancel", custom_id='noBtn')
	await ctx.send("Are you sure you paid ? Check your payment app before proceeding\n-# Repeated payment failure can lead to ban", components=[yesBtn, noBtn])


yesBtn_regex_pattern = re.compile(r"yesBtn_([0-9]+)_([0-9]+)")
@interactions.component_callback(yesBtn_regex_pattern)
async def yesBtn_callback(ctx):
	match = yesBtn_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
		pay_index = match.group(2)
	print('yes button', ord_no, 'pay_index: ', pay_index)
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	doc_ref.set({f'half_paid_{pay_index}': [True, False]}, merge=True)
	recBtn = Button(style=ButtonStyle.GREEN, label="Recieved", custom_id=f'recBtn_{ord_no}_{pay_index}')
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(doc_data['deliverer'])
	if guild_member!=None:
		member_dm = await guild_member.fetch_dm()
		await member_dm.send(f"Payment has been credited to your UPI for the order *[{ord_no}]*. Please check your payments App and Acknowledge whether you have recieved the payment to proceed.", components=[recBtn])
	await ctx.message.delete()


recBtn_regex_pattern = re.compile(r"recBtn_([0-9]+)_([0-9]+)")
@interactions.component_callback(recBtn_regex_pattern)
async def recBtn_callback(ctx):
	await ctx.defer()
	print("recived clicked")
	match = recBtn_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
		pay_index = match.group(2)
	print('rec button', ord_no, 'pay_index: ', pay_index)
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	cust_id=doc_data['customer']
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(cust_id)
	if guild_member!=None:
		member_dm = await guild_member.fetch_dm()
		if int(pay_index)==1:
			await member_dm.send(f"Payment has been verified. Food is on the way 🍽️")
			pickBtn = Button(style=ButtonStyle.PRIMARY, label="Yep, I Picked", custom_id=f'pickBtn_{ord_no}')
			await ctx.send(f"Great !!\nJust let us know when you have picked the order from the shop. 😀\nOrder no. *[{ord_no}]*", components=[pickBtn])
		else:
			await member_dm.send("Payment has been verified. Bon Appetite 🍽️")
			deliBtn = Button(style=ButtonStyle.PRIMARY, label="Yep, Mission successful", custom_id=f'deliBtn_{ord_no}')
			await ctx.send(f"Nice !!\nJust let us know when you have Delivered the order. 😀\nOrder no. *[{ord_no}]*", components=[deliBtn])
	await ctx.message.delete()
	doc_ref.set({f'half_paid_{pay_index}': [True, True]}, merge=True)


pickBtn_regex_pattern = re.compile(r"pickBtn_([0-9]+)")
@interactions.component_callback(pickBtn_regex_pattern)
async def pickBtn_callback(ctx):
	match = pickBtn_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
	print('pick button', ord_no)
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	cashBtn = Button(style=ButtonStyle.SECONDARY, label="Cash", custom_id=f'pay2mode_{ord_no}_1')
	onlnBtn = Button(style=ButtonStyle.PRIMARY, label="GPay", custom_id=f'pay2mode_{ord_no}_2')
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(doc_data['customer'])
	if guild_member!=None:
		member_dm = await guild_member.fetch_dm()
		await member_dm.send(f"<@{doc_data['deliverer']}> has pickked your order.\nHow do you wish to pay the balance ?", components=[onlnBtn, cashBtn])
	doc_ref.set({'status': 'picked'}, merge=True)
	pickedBtn = Button(custom_id="picked_btn", style=ButtonStyle.SECONDARY, label="Picked", disabled=True, emoji="👍")
	await ctx.edit_origin(components=[pickedBtn])


pay2mode_regex_pattern = re.compile(r"pay2mode_([0-9]+)_([0-9]+)")
@interactions.component_callback(pay2mode_regex_pattern)
async def pay2mode_callback(ctx):
	match = pay2mode_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
		mode = match.group(2)
	print('pay2mode', ord_no, 'mode:', mode)
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	deliBtn = Button(style=ButtonStyle.PRIMARY, label="Yep, Mission successful", custom_id=f'deliBtn_{ord_no}')
	if mode=='1':
		guild = await ctx.bot.fetch_guild(ids_json['server_id'])
		guild_member = await guild.fetch_member(doc_data['deliverer'])
		if guild_member!=None:
			member_dm = await guild_member.fetch_dm()
			await member_dm.send(f"💸 Balance payment will be done in cash on delivery.\nClick the below button once the delivery is complete.", components=[deliBtn])
		doc_ref.set({'half_paid_2': 'cash'}, merge=True)
	else:
		user_dic = db.collection('Users').document(str(ctx.user.id)).get().to_dict()
		adv_amt=int(doc_data['topay']/2)+1
		url_string = f"upi://pay?pa={user_dic['upi']}&am={adv_amt}&tn=Order{ord_no}_adv&cu=INR"
		encoded_path = urllib.parse.quote(url_string, safe='')
		redirect_url = f"https://pver-programz.github.io/url-redirector/?url={encoded_path}"
		embed = interactions.Embed(
				title="Payment Screen",
				description="Balance payment.",
				color=0xFAD35C,
				url=redirect_url,
			)
		embed.add_field(
			name="Amount",
			value=f"₹ {adv_amt}",
			inline=True,
			)
		embed.add_field(
			name="Payment QR",
			value=f"Pay via UPI",
			inline=True,
			)
		embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=225x225&data={encoded_path}")
		payBtn = Button(url=redirect_url, style=ButtonStyle.URL, label="Pay")
		veriBtn = Button(style=ButtonStyle.SECONDARY, label="Verify Payment", custom_id=f'veriBtn_{ord_no}_2')
		await ctx.edit_origin(content='Order Picked. Complete Balance payment.', embed=embed, components=[payBtn, veriBtn])

deliBtn_regex_pattern = re.compile(r"deliBtn_([0-9]+)")
@interactions.component_callback(deliBtn_regex_pattern)
async def deliBtn_callback(ctx):
	match = deliBtn_regex_pattern.match(ctx.custom_id)
	if match:
		ord_no = match.group(1)
	print("deli butn", ord_no)
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	guild = await ctx.bot.fetch_guild(ids_json['server_id'])
	guild_member = await guild.fetch_member(doc_data['customer'])
	if guild_member!=None:
		member_dm = await guild_member.fetch_dm()
		await member_dm.send(f"{ctx.user.mention} has just delivered your order. 😀\n||Incase of disputes use </support:12345>||")
	doc_ref.set({'status': 'delivered'}, merge=True)
	await ctx.send("Thank you for your service 🫡")
	await ctx.message.delete()



@interactions.component_callback('noBtn')
async def noBtn_callback(ctx):
	await ctx.send("Pay and Verify again.", delete_after=5)
	await ctx.message.delete()




@interactions.component_callback("viewdetails_button")
async def viewDet_button_callback(ctx: interactions.ComponentContext):
	await ctx.defer(ephemeral=True)
	cont=ctx.message.content
	ord_no = cont[cont.index('[')+1:cont.index(']')]
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	if str(doc_data['customer'])!=str(ctx.user.id):
		topay = payable(int(doc_data['cart_total']), doc_data['drop_params'][0], doc_data['drop_params'][1], sum(doc_data['cart'].values()), doc_data['drop_params'][2])
		add_text = f"Order No. *[{ord_no}]*\nDrop-point: **{doc_data['drop'][0]} {doc_data['drop'][1]}**\n{doc_data['instruction']}"
		add_text=add_text+f"\nEstimated delivery bonus: **{topay[2]:.2f}% - {topay[2]+10:.2f}%** of order value"
		await ctx.send(add_text, ephemeral=True)
	else:
		# print(str(doc_data['customer'])==str(ctx.user.id), str(doc_data['customer']), str(ctx.user.id))
		guild = await ctx.bot.fetch_guild(ids_json['server_id'])
		guild_member = await guild.fetch_member(ctx.user.id)
		if guild_member!=None:
			cust_dm = await guild_member.fetch_dm()
		link = cust_dm.get_message(doc_data['user_dm_msgid']).jump_url
		await ctx.send(f"Details have been DMed to you\n{link}", ephemeral=True)


@interactions.component_callback("dec_button")
async def dec_button_callback(ctx: interactions.ComponentContext):
	cont=ctx.message.content
	ord_no = cont[cont.index('[')+1:cont.index(']')]
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	doc_data['requestees'][str(ctx.user.id)]=firestore.DELETE_FIELD
	doc_ref.set({'requestees': doc_data['requestees']}, merge=True)
	await ctx.message.edit(components=declinedBtn)

@interactions.component_callback("upd_button")
async def upd_button_callback(ctx: interactions.ComponentContext):
	cont=ctx.message.content
	ord_no = cont[cont.index('[')+1:cont.index(']')]
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	stat_list=[]
	deli_text=''
	if doc_data['status']=='open':
		stat_list.append('✅')
		for x in range(7):
			stat_list.append('❌')
	elif doc_data['status']=='due':
		for x in range(2):
			stat_list.append('✅')
		deli_text=f"\nDelivery by <@{doc_data['deliverer']}>"
		stat_list.append("✅" if doc_data['half_paid_1'][0] else '❌')
		stat_list.append("✅" if doc_data['half_paid_1'][1] else '❌')
		for x in range(4):
			stat_list.append('❌')
	elif doc_data['status']=='picked':
		for x in range(5):
			stat_list.append('✅')
		try:
			stat_list.append("✅" if doc_data['half_paid_2'][0] else '❌')
			stat_list.append("✅" if doc_data['half_paid_2'][1] else '❌')
		except:
			stat_list.append('✅')
			stat_list.append('✅')
		stat_list.append('❌')
	elif doc_data['status']=='delivered':
		for x in range(8):
			stat_list.append('✅')
	else:
		print(f"Error occured in status update for {ord_no}")
		await ctx.send("ERROR Occured")
	text = f'''
Order No. *[{ord_no}]*
{stat_list[0]}	Order Placed on <t:{ord_no}>
{stat_list[1]}	Deliverer Accepted{deli_text}
{stat_list[2]}	Advance Paid by Customer
{stat_list[3]}	Advance Recieved by Deliverer
{stat_list[4]}	Order Picked up
{stat_list[5]}	Payment Completed by Customer
{stat_list[6]}	Payment Recieved by Deliverer
{stat_list[7]}	Delivered
	'''.strip()
	await ctx.send(text, delete_after=30)

@interactions.component_callback("canc_button")
async def canc_button_callback(ctx: interactions.ComponentContext):
	cont=ctx.message.content
	ord_no = cont[cont.index('[')+1:cont.index(']')]
	doc_ref = db.collection('orders').document(ord_no)
	doc_data = doc_ref.get().to_dict()
	if doc_data['status']=='open':
		await ctx.message.edit(components=canceledBtn)
		await bot.get_channel(ids_json['order_channel']).get_message(doc_data['ord_chan_msgid']).edit(components=canceledBtn)
		for requestee_id in doc_data['requestees']:
			guild = await ctx.bot.fetch_guild(ids_json['server_id'])
			guild_member = await guild.fetch_member(requestee_id)
			if guild_member!=None:
				member_dm = await guild_member.fetch_dm()
				await member_dm.get_message(doc_data['requestees'][requestee_id]).edit(components=canceledBtn)
		doc_ref.set({'status': 'cancelled'}, merge=True)
	else:
		update_button = Button(style=ButtonStyle.PRIMARY, label="Order Status", custom_id="upd_button")
		canc_button = Button(style=ButtonStyle.DANGER, label="Cancel", custom_id="canc_button", disabled=True)
		userDmRow = ActionRow(update_button, canc_button)
		await ctx.message.edit(components=userDmRow)
		await ctx.send("It's too late to cancel now.")

bot.start()


'''
TODO:
order status update
Payment not recieved screenshot - message context menu
complaint ticket raising system
Line 1205 deliBtn_callback - support command id
'''