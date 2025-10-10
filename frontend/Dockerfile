FROM node:22.12.0

WORKDIR /app

# העתק רק את קבצי ההתקנה בשלב ראשון
COPY package*.json ./

# התקנת תלויות *בתוך* דוקר
RUN npm install

# העתק את כל שאר הקבצים
COPY . .

# פורט הריצה של Vite
EXPOSE 5173

# הפעלת הפיתוח עם host פתוח
CMD ["npm", "run", "dev", "--", "--host"]
