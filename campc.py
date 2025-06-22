import interactions
from interactions import Button, ButtonStyle, ActionRow
from interactions.ext.paginators import Paginator
from interactions.api.events import Component
import firebase_admin
from firebase_admin import credentials, firestore, auth
import math
import time
import mial
import requests
from random import choice as rand
import json

with open("tokens.json", 'r') as f:
	tok_json = json.load(f)
TOKEN = tok_json['bot']
FIREBASE_WEB_API_KEY = tok_json['gservice']

with open("discord_ids.json", 'r') as f:
	ids_json = json.load(f)


bot = interactions.Client(token=TOKEN)

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
		await ctx.send("🚫 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"🚫 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>")
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
	try:
		member_roles = [role.id for role in guild_member.roles]
	except AttributeError:
		await ctx.send("🚫 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"🚫 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>")
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
			if name == None and phone_number == None and upi_id == None and hosteller == None and gender == None:
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
		await ctx.send("🚫 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"🚫 Access Denied! You need to be registered to use this command. Use </register:1385296092232552573>")
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
		value="Hosteller" if user_data['hosteller'] else "Dayscholar",
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
	if "@" in user_data['upi'] and " " not in user_data['upi'].strip():
		embed.set_image(url=f"https://api.qrserver.com/v1/create-qr-code/?size=225x225&data={user_data['upi']}")
	else:
		embed.set_image(url=f"https://placehold.co/600x300/FF0000/FFFFFF.png?text=UPI_not_set")
	await ctx.send(embed=embed, ephemeral=True)


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
async def register(ctx: interactions.SlashContext):
	reg_modal = interactions.Modal(
		interactions.ShortText(label="Your VIT Email", custom_id="reg_short_text"),
		title="Register User",
		custom_id="reg_modal",
	)
	await ctx.send_modal(modal=reg_modal)
	modal_ctx: interactions.ModalContext = await ctx.bot.wait_for_modal(reg_modal)
	email = modal_ctx.responses["reg_short_text"]
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
				await modal_ctx.send(f"User with email `{email[:4]}****@vitstudent.ac.in` already exists. and registered to {disids}")
			else:
				if send_reset_link(email):
					await modal_ctx.send("Check your email for a password reset link. Set your passwaord as your discord username and then Use </connect:1385296092232552574> to connect your discord to Sloth App.", components=[gmailBtn])
				else:
					await modal_ctx.send("Registration ERROR: Unable to send verification mail.")
				# link = auth.generate_password_reset_link(email)
				# await modal_ctx.send(f"user {user.uid} \n link {link}", components=[gmailBtn, connectBtn])
		except auth.UserNotFoundError:
			user = auth.create_user(email=email,password=email[::-1])
			if send_reset_link(email):
				await modal_ctx.send("Check your email for a password reset link. Set your passwaord as your discord username and then Use </connect:1385296092232552574> to connect your discord to Sloth App.", components=[gmailBtn])
			else:
				await modal_ctx.send("Registration ERROR: Unable to send verification mail.")
			# link = auth.generate_password_reset_link(email)
			# message = await modal_ctx.send(f"user {user.uid} \n link {link}", components=[gmailBtn, connectBtn])
		except:
			await ctx.send("ERROR Occured. Please Try Again")
	else:
		await modal_ctx.send("Use VIT student email.")


@interactions.slash_command(name="connect", description="Verifies your discord so that you can place orders")
async def connect(ctx: interactions.SlashContext):
	con_modal = interactions.Modal(
		interactions.ShortText(label="Re-Enter your VIT Email", custom_id="con_short_text"),
		title="Register User",
		custom_id="con_modal",
	)
	await ctx.send_modal(modal=con_modal)
	modal_ctx: interactions.ModalContext = await ctx.bot.wait_for_modal(con_modal)
	email = modal_ctx.responses["con_short_text"]
	users_collection = db.collection("Users")
	if users_collection.document(str(ctx.user.id)).get().exists:
		await modal_ctx.send("🤡 User already connected")
	else:
		if email.strip().endswith("@vitstudent.ac.in"):
			try:
				testuser = auth.get_user_by_email(email)
				if sign_in_with_email_and_password(email, ctx.user.username):
					dis_uid=ctx.user.id
					member = ctx.guild.get_member(dis_uid)
					user_data = {"email": email, "username": ctx.user.username, "in_deli": False, "can_deli": True, 'cart':{},
								# "name": email[:email.index('20')], "phone": '0000000000', "upi": "not_set", "profile_completion": (2/4)*100}
								"name": email[:email.index('@')], "phone": '0000000000', "upi": "not_set", "profile_completion": int((1/6)*100),
								"gender": None, "hosteller": None}
					users_collection.document(str(ctx.user.id)).set(user_data)
					await member.add_role(ids_json['veri_role'])
					await modal_ctx.send(f"<@{dis_uid}> Just got Verified 🏆")
				else:
					await modal_ctx.send("Unable Verify. If this Email is registered, check mail for password reset link. Set your passwaord as your discord username and then retry.")
			except auth.UserNotFoundError:
				await modal_ctx.send("Invalid Email: This Email is not registered.")
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
		await ctx.send("🚫 You need to be member of main server to access this command.\nJoin: https://discord.gg/gDsbveRBDx")
		return
	if ids_json['veri_role'] not in member_roles:
		await ctx.send(f"🚫 Access Denied! You need to be registered to use this command. Clcik </register:1385296092232552573>")
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
		else:
			cart = {}
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
		for x in cart:
			dish_data = menu_col.document(cart_res).get().to_dict()[x]
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

		user_doc = db.collection("Users").document(str(ctx.user.id))
		try:
			sel_res_placehold = user_data['cart_res']
		except KeyError:
			sel_res_placehold = list(res_data.keys())[-1]
		user_doc.set({'selected_dishes':None, 'selected_count': 1, 'selected_res': sel_res_placehold, 'cart_total': tot_cost}, merge=True)
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


# global_users = {}

@interactions.component_callback("res_men")
async def res_men_callback(ctx):
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values[0]
	user_doc.set({'selected_res':f'{choice}'}, merge=True)
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
	await ctx.edit_origin(content = f"Selected Restraunt: {choice}", components=components)

@interactions.component_callback("dish_men")
async def dish_men_callback(ctx):
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values
	user_doc.set({'selected_dishes':choice}, merge=True)
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
		ph=''
		for x in choice:
			if len(ph)<145:
				ph+=x+', '
			else:
				ph+='...'
				break
		else:
			ph=ph[:-2]
		actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=ph, custom_id="dish_men", min_values=1, max_values=1))
		# actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=ph, custom_id="dish_men", min_values=1, max_values=len(user_dic['selactable_dislis'])))
	except KeyError:
		actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
		# actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=len(dislis)))
	actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder="How many to buy ?", custom_id="dish_cou", min_values=1, max_values=1))
	actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
	components=[actRow0, actRow1, actRow2, actRow3, actRow4]
	await ctx.edit_origin(content=f"Selected Dishes: {choice}", components=components)

@interactions.component_callback("dish_cou")
async def dish_cou_callback(ctx):
	user_doc = db.collection("Users").document(str(ctx.user.id))
	choice = ctx.values[0]
	user_doc.set({'selected_count':int(choice)}, merge=True)
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
		prod_string=""
		for x in user_dic['selected_dishes']:
			if len(prod_string)<145:
				prod_string+=x+', '
			else:
				prod_string+='...'
				break
		else:
			prod_string=prod_string[:-2]
		actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=prod_string, custom_id="dish_men", min_values=1, max_values=1))
		# actRow2 = ActionRow(interactions.StringSelectMenu(*user_dic['selactable_dislis'], placeholder=prod_string, custom_id="dish_men", min_values=1, max_values=len(user_dic['selactable_dislis'])))
	except KeyError:
		actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=1))
		# actRow2 = ActionRow(interactions.StringSelectMenu(*list(res_data[list(res_data.keys())[-1]].keys()), placeholder="Choose to Buy what ?", custom_id="dish_men", min_values=1, max_values=len(list(res_data[list(res_data.keys())[-1]].keys()))))
	actRow3 = ActionRow(interactions.StringSelectMenu(['1', '2', '3', '4', '5'], placeholder=f"{choice}", custom_id="dish_cou", min_values=1, max_values=1))
	actRow4 = ActionRow(add2cart_button, remove_from_cart_button)
	components=[actRow0, actRow1, actRow2, actRow3, actRow4]
	await ctx.edit_origin(content=f"Selected Dishes will be added/removed {choice} times to your cart", components=components)

@interactions.component_callback("a2c_button")
async def a2c_callback(ctx):
	await ctx.defer(edit_origin=True)
	user_doc = db.collection("Users").document(str(ctx.user.id))
	user_dic = user_doc.get().to_dict()
	res_change=False
	if user_dic['selected_dishes'] is not None:
		new_cart_res = None
		try:
			if user_dic['cart_res'] != user_dic['selected_res']:
				user_dic['cart']={}
				user_doc.set({'cart_res':user_dic['selected_res'], 'cart': user_dic['cart'], 'selected_count':1}, merge=True)
				# await ctx.edit_origin(content =f"Selected Restraunt is changed to {user_dic['selected_res']}. Cart Cleared.")
				res_change=True
			for x in user_dic['selected_dishes']:
				try:
					user_dic['cart'][f"{x}"] += user_dic['selected_count']
				except KeyError as e:
					if str(e)==f"'{x}'":
						user_dic['cart'][f"{x}"] = user_dic['selected_count']
					elif e=='selected_count':
						user_dic['cart'][f"{x}"] = 1
					else:
						print(e, type(e), x)
		except KeyError:
			print("restraunt changed")
		###############
		cart=user_dic['cart']
		cart_res=user_dic['selected_res']
		menu_col = db.collection("Menu")
		embed = interactions.Embed(title="Cart View", description=f"Cart Size: {len(cart)}", color=0xFAD35C)
		embed.set_author(name=ctx.user.username, icon_url=ctx.user.avatar.url)
		if len(cart)!=0:
			embed.set_thumbnail(url=f"https://placehold.co/128x128/FAD35C/000000.png?text={cart_res}") ########## A2C
		tot_cost=0
		for x in cart:
			dish_data = menu_col.document(cart_res).get().to_dict()[x]
			avail = "✅" if dish_data[1] else "🔴"
			embed.add_field(
				name=f"{x} [{cart[x]}]",
				value=f"""Cost: ₹{dish_data[0]} - Availablity: {avail}""",
				inline=False,
			)
			tot_cost+=dish_data[0]*cart[x]
		embed.set_footer(text=f"Total Cost: ₹{tot_cost}")
		user_doc.set({'cart':user_dic['cart'], 'cart_res':new_cart_res, 'cart_total': tot_cost}, merge=True)
		if res_change:
			await ctx.edit_origin(content =f"Selected Restraunt is changed to {user_dic['selected_res']}. Cart Cleared.", embed=embed)
		else:
			await ctx.edit_origin(content="Use </menu:1385296092232552569> to view available dishes to order", embed=embed)	
	else:
		await ctx.send(f"<@{ctx.user.id}>\n ‼ Please select Product to add to cart.", ephemeral=True)

@interactions.component_callback("r2c_button")
async def r2c_callback(ctx):
	user_doc = db.collection("Users").document(str(ctx.user.id))
	user_dic = user_doc.get().to_dict()
	for x in user_dic['selected_dishes']:
		try:
			user_dic['cart'][f"{x}"] -= user_dic['selected_count']
			if user_dic['cart'][f"{x}"] <= 0:
				user_dic['cart'][f"{x}"] = firestore.DELETE_FIELD
		except KeyError as e:
			await ctx.send(f"{user_dic['selected_dishes']} is not in cart to remove", delete_after=2, ephemeral=True)
			return
	cart=user_dic['cart']
	cart_res=user_dic['selected_res']
	menu_col = db.collection("Menu")
	embed = interactions.Embed(title="Cart View", description=f"Cart Size: {len(cart)}", color=0xFAD35C)
	embed.set_author(name=ctx.user.username, icon_url=ctx.user.avatar.url)
	if len(cart)!=0:
		embed.set_thumbnail(url=f"https://placehold.co/128x128/FAD35C/000000.png?text={cart_res}") ########## A2C
	tot_cost=0
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
		except:
			pass
	user_doc.set({'cart':user_dic['cart'], 'cart_total':tot_cost}, merge=True)
	embed.set_footer(text=f"Total Cost: ₹{tot_cost}")
	await ctx.edit_origin(content="Use </menu:1385296092232552569> to view available dishes to order", embed=embed)	


@interactions.component_callback("buy_button")
async def buy_button_callback(ctx: interactions.ComponentContext):
	ph = rand(["It's my Lunch. Bring ASAP Please.", "Drop by 2 PM.", "Don't forget ketchup", "Enjoy extra tips", "2 More Spoons please"])
	ord_modal = interactions.Modal(
		interactions.ShortText(label="Drop Point Room no.", custom_id="drop_text", required=True, placeholder="Example: AB-1 708"),
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
		await ctx.send(f"{ctx.user.mention}\n📉 Your profile is not Complete. Complete Your profile using </profile edit:1385296092232552570>.\nCurrent Profile Completion: **{user_data['profile_completion']}**%")


@interactions.modal_callback("ord_modal")
async def on_modal_answer(ctx: interactions.ModalContext, drop_text: str, inst_text: str):
	ord_no = int(time.time())
	orders_doc = db.collection("orders").document('open')
	try:
		users_ref = db.collection('Users')
		query = users_ref.where('can_deli', '==', True).stream()
		requested_users_id_msgs = {}
		acc_button = Button(style=ButtonStyle.GREEN, label="Accept", custom_id="acc_button")
		dec_button = Button(style=ButtonStyle.DANGER, label="Decline", custom_id="dec_button")
		dec_button_chan = Button(style=ButtonStyle.DANGER, label="Decline", custom_id="dec_button_chan")
		for doc in query:
			if doc.id != ctx.user.id:
				guild = await ctx.bot.fetch_guild(ids_json['server_id'])
				guild_member = await guild.fetch_member(int(doc.id))
				if guild_member!=None:
					member_dm = await guild_member.fetch_dm()
					dm_message = await member_dm.send("Are you willing to deliver ?", components=[acc_button, dec_button])
					requested_users_id_msgs[doc.id]=dm_message.id
					print("DMed:", guild_member.tag)
				else:
					print("Not member:", guild_member.tag)
		update_button = Button(style=ButtonStyle.PRIMARY, label="Order Status", custom_id="upd_button")
		canc_button = Button(style=ButtonStyle.DANGER, label="Cancel", custom_id="canc_button")
		userDmRow = ActionRow(update_button, canc_button)
		user_dm = ctx.user.fetch_dm()
		user_dm.send("You have ordered this", components=[userDmRow])
		ord_chan_message = await bot.get_channel(ids_json['order_channel']).send(f"{ctx.user.mention} Order No. *{ord_no}* \nDelivery to **{drop_text}**\n{inst_text}", components=[acc_button, dec_button_chan])
		ord_details={'customer':ctx.user.id, 'drop':drop_text, 'instruction':inst_text, 'requestees':requested_users_id_msgs}
		orders_doc.set({ord_no: ord_details}, merge=True)
		await modal_ctx.send("Fetching the Perfect person for you.")
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

		await ctx.edit_origin(embeds=new_embed, components=[])
	except:
		await ctx.send("ERROR: Unable to Clear Cart")


@interactions.component_callback("acc_button")
async def clear_button_callback(ctx: interactions.ComponentContext):
	await ctx.send("Accept Button")

@interactions.component_callback("acc_button")
async def clear_button_callback(ctx: interactions.ComponentContext):
	await ctx.send("Decline Button")

bot.start()
