import { useEffect, useRef, useState, useCallback } from "react";
import { useAuth } from "../lib/auth";
import { useNavigate } from "react-router-dom";

const BACKEND = "https://ancestral-sage-backend.onrender.com";

function useKeepAlive() {
  useEffect(() => {
    const ping = () => fetch(`${BACKEND}/api/health`, { method:"GET" }).catch(()=>{});
    ping();
    const id = setInterval(ping, 14 * 60 * 1000);
    return () => clearInterval(id);
  }, []);
}

export default function Helper({ requireAuth = false }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  useKeepAlive();

  useEffect(() => {
    const fab = document.getElementById("wai-helper-fab");
    if (fab) fab.style.display = "none";
    return () => { if (fab) fab.style.display = ""; };
  }, []);

  if (loading) return (
    <div style={{display:"flex",alignItems:"center",justifyContent:"center",height:"100vh",fontFamily:"system-ui"}}>
      Loading...
    </div>
  );
  if (requireAuth && !user) { navigate("/login"); return null; }
  return requireAuth ? <AuthHelper user={user} /> : <PublicHelper />;
}

// ===========================================================================
// KNOWLEDGE BASE - structured facts for each category
// Used by smart fallback when AI is unavailable
// ===========================================================================
const KB = {
  mail: {
    keywords: ["mail","letter","notice","envelope","correspondence","received","document","paper","sent me"],
    facts: [
      "Official letters always include your full name, address, and a return address from the sender.",
      "Government letters from IRS, SSA, or courts come by postal mail - not email or text.",
      "If a letter demands immediate payment or threatens arrest, that is almost always a scam.",
      "You have the right to request written verification of any debt within 30 days of first contact.",
      "Certified mail requires your signature - if you missed it, the post office holds it for 15 days.",
      "Jury duty notices come from your local courthouse - they are real and must be responded to.",
      "If you receive someone else's mail, do not open it - write 'return to sender' and put it back.",
      "Medical bills often have errors - you have the right to request an itemized bill and dispute charges.",
      "Utility disconnection notices must give you at least 10 days warning by law in most states.",
      "A demand letter from an attorney is not a court order - you have time to respond or seek legal help.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("irs") || ql.includes("tax")) return "IRS letters are always sent by postal mail - never email or phone. The letter will have your partial Social Security number and a notice number in the top right corner. Real IRS letters give you time to respond - usually 30-60 days. If someone called claiming to be the IRS and demanded immediate payment, that is a scam. Call 1-800-829-1040 to verify any IRS contact.";
      if (ql.includes("jury") || ql.includes("court")) return "Jury duty notices are real legal obligations. The notice will have your local courthouse name, a reporting date, and instructions. You can request a postponement online or by mail if you have a hardship. Missing jury duty without response can result in a fine. Call the number on the notice to ask about postponement options.";
      if (ql.includes("debt") || ql.includes("collection") || ql.includes("collector")) return "Debt collection letters must identify the creditor, the amount, and your right to dispute. You have 30 days to send a written dispute and request verification. Once you dispute in writing, the collector must stop contact until they verify the debt. Keep a copy of everything you send. Never pay a debt you do not recognize without getting written verification first.";
      if (ql.includes("evict") || ql.includes("landlord")) return "An eviction notice is a legal document that starts a process - it does not mean you have to leave immediately. Most states require a notice period of 3 to 30 days depending on the reason. You have the right to respond and contest the eviction in court. Contact a local tenant rights organization or legal aid immediately - many offer free help and can appear in court with you.";
      return "To help you understand this letter, I need to know a few things: Who sent it? What is the main thing it is asking you to do? Is there a deadline or date mentioned? Once you share those details I can explain exactly what it means and what steps to take.";
    }
  },
  bills: {
    keywords: ["bill","owe","charge","payment","debt","amount","balance","invoice","statement","overdue","past due","utility","electric","water","gas","phone","internet"],
    facts: [
      "You have the right to request an itemized bill from any provider - this shows every individual charge.",
      "Billing errors are common - studies show 80% of medical bills contain errors.",
      "You can dispute a charge in writing within 60 days for credit card bills under the Fair Credit Billing Act.",
      "Utilities cannot shut off service without proper notice - usually 10-14 days depending on your state.",
      "If you cannot pay, call the company before the due date - most have hardship programs or payment plans.",
      "Medical debt under $500 no longer appears on credit reports as of 2023.",
      "You can negotiate medical bills - hospitals often accept 20-50% of the original amount.",
      "If a bill goes to collections, the original due date is what affects your credit - not the collection date.",
      "Low-income households may qualify for LIHEAP - a federal program that helps pay energy bills.",
      "Internet providers offer low-cost plans through the Affordable Connectivity Program for qualifying households.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("medical") || ql.includes("hospital") || ql.includes("doctor")) return "Medical bills can be negotiated and often contain errors. First, request an itemized bill - this lists every charge separately. Compare it against your insurance Explanation of Benefits (EOB). If something looks wrong, call the billing department and ask them to explain each charge. Most hospitals have financial assistance or charity care programs - ask specifically for the financial assistance office. You can often negotiate the total down by 20-50% if you offer to pay in a lump sum.";
      if (ql.includes("electric") || ql.includes("utility") || ql.includes("gas") || ql.includes("water")) return "Utility companies cannot shut off your service without a written notice at least 10-14 days in advance. Before shut-off you have the right to a payment plan. Call the company and ask about hardship programs, budget billing, or deferred payment plans. The LIHEAP program (Low Income Home Energy Assistance Program) provides federal help with energy bills - call 211 to apply or find your local office.";
      if (ql.includes("credit card") || ql.includes("credit")) return "For credit card billing errors, you can dispute a charge within 60 days of the statement date in writing. Send your dispute by certified mail to the billing address. The card company must investigate within 30 days and cannot try to collect the disputed amount during investigation. If the charge is fraudulent, report it as fraud - your liability is limited to $50 by law, and most cards offer zero liability.";
      if (ql.includes("collection") || ql.includes("collector")) return "When a bill goes to collections, you still have rights. Request debt verification in writing within 30 days. Once you dispute in writing, they must stop collecting until they verify. After 7 years, most debts fall off your credit report. You can also negotiate a settlement for less than the full amount, or a pay-for-delete agreement where they remove the collection from your credit in exchange for payment.";
      return "To help you with this bill, tell me: who sent it, what the amount is, and if there is anything on it that does not look right. Everyone has the right to an itemized bill and to dispute charges they do not recognize. If you cannot pay the full amount, most companies have payment plans - I can help you figure out how to ask for one.";
    }
  },
  housing: {
    keywords: ["evict","eviction","rent","lease","landlord","tenant","apartment","house","housing","notice","deposit","security deposit","move out","move in","repair","maintenance"],
    facts: [
      "Landlords must give written notice before entering your home - usually 24-48 hours except in emergencies.",
      "Security deposits must be returned within 14-30 days of move-out depending on your state.",
      "Landlords cannot retaliate against you for reporting code violations or forming a tenant union.",
      "An eviction requires a court order - a landlord cannot change your locks or remove your belongings without one.",
      "Habitability standards require landlords to maintain heat, water, and a structurally safe home.",
      "Section 8 and Housing Choice Vouchers can significantly reduce rent for qualifying households.",
      "You can withhold rent or repair-and-deduct in some states if landlord refuses to fix serious problems.",
      "A lease is a legal contract - read it carefully before signing, especially the break lease terms.",
      "Most cities have tenant rights hotlines that offer free advice - call 211 to find yours.",
      "Rental assistance programs exist in most counties - 211 can connect you to local help.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("evict") || ql.includes("notice to vacate") || ql.includes("pay or quit")) return "An eviction notice is the start of a legal process - not an order to leave immediately. Here are your rights: The landlord must file in court and a judge must issue an order before you legally have to leave. You have the right to attend the hearing and present your case. Common defenses include: landlord failed to maintain the property, landlord did not follow proper notice procedures, you paid the rent and have proof, or the eviction is retaliatory. Contact legal aid or a tenant rights organization today - many will represent you for free. Call 211 for local resources.";
      if (ql.includes("deposit") || ql.includes("security")) return "Security deposit rules vary by state but landlords generally must return your deposit within 14-30 days of move-out. They can only deduct for unpaid rent, damage beyond normal wear and tear, and cleaning if specified in your lease. They must provide an itemized written list of any deductions. If they do not return your deposit within the deadline without proper documentation, you may be entitled to double or triple the amount in small claims court. Document the condition of the apartment when you move in and out with photos.";
      if (ql.includes("repair") || ql.includes("maintenance") || ql.includes("broken") || ql.includes("heat") || ql.includes("mold")) return "Landlords are legally required to maintain habitable conditions including working heat, running water, no mold, and structural safety. To protect yourself: send repair requests in writing by email or text so you have a record, keep copies of everything. If the landlord does not respond within a reasonable time, you can report the violation to your local housing authority or code enforcement. In some states you can legally withhold rent or pay for repairs yourself and deduct from rent - check your state's laws or call a tenant hotline first.";
      return "Housing issues are serious and you have more rights than most people realize. Tell me more about your situation - are you dealing with an eviction notice, a landlord not making repairs, a security deposit problem, or something else? The more you share the better I can explain your options and rights.";
    }
  },
  legal: {
    keywords: ["court","lawyer","attorney","lawsuit","sue","legal","judge","case","hearing","summons","subpoena","warrant","rights","arrested","charged","criminal","civil","small claims","divorce","child support","alimony","bankruptcy","lien"],
    facts: [
      "You have the right to remain silent and the right to an attorney if arrested.",
      "Free legal aid is available in every state for people who cannot afford an attorney.",
      "Small claims court handles disputes up to $5,000-$25,000 depending on your state - no lawyer needed.",
      "A summons requires you to respond within a specific time - ignoring it results in a default judgment against you.",
      "You cannot be jailed for owing a private debt - only for criminal contempt of court or unpaid child support.",
      "Bankruptcy can discharge most unsecured debts including credit cards and medical bills.",
      "A power of attorney lets you designate someone to make decisions on your behalf.",
      "Legal aid organizations offer free civil legal help to qualifying low-income individuals.",
      "You have 3 years in most states to file a personal injury lawsuit - this is called the statute of limitations.",
      "Written contracts are much easier to enforce than verbal agreements.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("summons") || ql.includes("lawsuit") || ql.includes("sued") || ql.includes("served")) return "If you received a summons, do not ignore it - ignoring a summons results in a default judgment against you, which can lead to wage garnishment or bank account freezes. You typically have 20-30 days to respond in writing. Contact a legal aid organization immediately - many provide free help for people facing lawsuits. If you cannot afford an attorney, you can represent yourself (pro se) and the court clerk can explain the process. Write down the deadline on the summons right now so you do not miss it.";
      if (ql.includes("arrest") || ql.includes("police") || ql.includes("criminal") || ql.includes("charged")) return "If you are facing criminal charges, your most important rights are: the right to remain silent (anything you say can be used against you), the right to an attorney (if you cannot afford one, the court must appoint one), and the right to a hearing before a judge. Do not discuss your case with anyone except your attorney. Public defenders are available for criminal cases if you cannot afford a lawyer. Contact your local public defender's office as soon as possible.";
      if (ql.includes("divorce") || ql.includes("separation") || ql.includes("custody") || ql.includes("child support")) return "Family law cases including divorce, custody, and child support are handled in family court. Most states allow you to represent yourself but it is complex, especially when children are involved. Legal aid organizations often have family law specialists. Mediation is usually cheaper than litigation for divorce. Child support is calculated by a formula in each state based on both parents' incomes. Courts always make decisions based on the best interest of the child.";
      if (ql.includes("small claims") || ql.includes("sue")) return "Small claims court is designed for everyday people without lawyers. You can sue for amounts typically between $2,500 and $25,000 depending on your state. The filing fee is usually $30-$100. You present your case directly to a judge with evidence like photos, receipts, and text messages. Common small claims cases include security deposit disputes, contractor disputes, and minor car accidents. Go to your local courthouse and ask for the small claims clerk to get the forms.";
      return "Legal situations can feel overwhelming but you have rights and there is free help available. Tell me more about what is happening - did you receive a court document, are you dealing with a specific legal situation, or do you need to find free legal help? Legal aid organizations in every city provide free help to people who qualify.";
    }
  },
  scam: {
    keywords: ["scam","fraud","fake","suspicious","gift card","wire transfer","western union","money gram","cryptocurrency","bitcoin","irs","social security","medicare","lottery","prize","winner","too good","urgent","immediately","threat","arrest","deportation","hack","phishing","email","text","call","robocall"],
    facts: [
      "The IRS never calls, emails, or texts demanding immediate payment - they always mail a letter first.",
      "Social Security never suspends your number or demands payment over the phone.",
      "No legitimate business or government agency will ever ask for payment in gift cards.",
      "If someone threatens arrest unless you pay immediately, it is almost certainly a scam.",
      "Grandparent scams call elderly people pretending to be a grandchild in trouble needing bail money.",
      "Romance scams cost Americans over $1.3 billion per year - anyone asking for money online is suspect.",
      "Medicare never calls asking for your card number - that is always fraud.",
      "Utility companies threatening immediate disconnection unless you pay by gift card is always a scam.",
      "Report scams to the FTC at reportfraud.ftc.gov and to your local police.",
      "If you already sent money in a scam, contact your bank immediately - some transfers can be reversed.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("gift card")) return "Anyone asking you to pay with gift cards is running a scam. This includes people claiming to be the IRS, Social Security, your utility company, a lawyer, the police, or even family members. Real government agencies and real businesses never accept gift cards as payment. Do not buy the cards. If you already bought them, do not read the numbers to anyone. Report this to the FTC at reportfraud.ftc.gov and to your local police. If you gave the numbers, call the gift card company's customer service number on the back of the card immediately - sometimes they can freeze unused funds.";
      if (ql.includes("irs") || ql.includes("tax")) return "The real IRS never calls, emails, or texts you demanding immediate payment. The IRS always sends a letter first through the postal mail. If someone called claiming to be the IRS and said you will be arrested if you do not pay right now, that is a scam. Hang up. The real IRS phone number is 1-800-829-1040. You can also verify any IRS contact by logging into your account at irs.gov. Report the scam call to the Treasury Inspector General at 1-800-366-4484.";
      if (ql.includes("social security") || ql.includes("ssa") || ql.includes("number suspended")) return "Social Security never suspends your Social Security number, never demands payment over the phone, and never threatens arrest. This is one of the most common scams targeting older Americans. Hang up on anyone making these claims. The real Social Security Administration number is 1-800-772-1213. Report the scam to the SSA Office of Inspector General at 1-800-269-0271 or at oig.ssa.gov.";
      if (ql.includes("lottery") || ql.includes("prize") || ql.includes("winner") || ql.includes("won")) return "Legitimate lotteries and sweepstakes never require you to pay a fee to receive your winnings. If you won a real prize, the taxes come out of the winnings automatically - you are never asked to pay upfront. The requirement to pay any fee, wire transfer, or buy gift cards to claim a prize is always a scam. Delete the message and do not respond. Report it to the FTC at reportfraud.ftc.gov.";
      return "What you are describing raises serious scam warning signs. Key scam signals are: demanding immediate action, threatening arrest or legal consequences, asking for gift cards or wire transfers, claiming to be the IRS or Social Security, and offering prizes you did not enter to win. Do not send any money, do not give personal information, and hang up or stop responding. Tell me more about what specifically happened and I can give you more specific guidance on what to do next.";
    }
  },
  employment: {
    keywords: ["job","work","fired","laid off","termination","unemployment","employer","employee","wage","salary","hours","overtime","discrimination","harassment","workplace","hr","human resources","resume","interview","benefits","w2","paystub","pay stub"],
    facts: [
      "Employees have the right to discuss their wages with coworkers - employers cannot legally prohibit this.",
      "Non-exempt employees must be paid time-and-a-half for hours over 40 per week under federal law.",
      "You can file for unemployment benefits within days of being laid off or wrongfully terminated.",
      "Employers must pay all earned wages on time - withholding wages is illegal.",
      "You have 180 days to file a discrimination complaint with the EEOC after the incident.",
      "At-will employment means you can be fired for any reason - but not for illegal reasons like discrimination.",
      "FMLA provides up to 12 weeks of unpaid protected leave for qualifying medical or family situations.",
      "Your employer must provide a W-2 by January 31st each year.",
      "Non-compete agreements are not enforceable in some states and must be reasonable in scope.",
      "You have the right to a safe workplace under OSHA regulations.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("fired") || ql.includes("terminated") || ql.includes("laid off")) return "Being fired or laid off is stressful but you likely have options. First, apply for unemployment benefits right away at your state's unemployment website - you can usually apply even if you were fired, unless it was for serious misconduct. Second, request your final paycheck in writing if you have not received it - employers must pay all earned wages by a specific deadline. Third, review any severance agreement carefully before signing - once you sign you usually waive your right to sue. Contact an employment attorney if you think the firing was discriminatory or retaliatory.";
      if (ql.includes("unemployment")) return "To apply for unemployment benefits, go to your state's workforce or labor department website. You will need your work history for the past 18 months, your Social Security number, and bank account information for direct deposit. Apply as soon as possible - there is usually a waiting week before benefits begin. Benefits typically replace 40-60% of your wages. You must be available and actively looking for work to continue receiving benefits. If your claim is denied, you have the right to appeal.";
      if (ql.includes("wage") || ql.includes("overtime") || ql.includes("not paid") || ql.includes("paycheck")) return "Wage theft is illegal. If your employer is not paying you correctly, you can file a complaint with your state labor board and with the federal Department of Labor Wage and Hour Division at dol.gov. Keep records of all your hours worked and pay received. Federal law requires time-and-a-half pay for hours over 40 per week for non-exempt workers. Your employer cannot retaliate against you for filing a wage complaint. Many employment attorneys take wage cases on contingency - meaning no upfront cost to you.";
      if (ql.includes("discriminat") || ql.includes("harass") || ql.includes("hostile")) return "Workplace discrimination and harassment based on race, color, religion, sex, national origin, age, or disability are illegal under federal law. Document everything: dates, times, witnesses, and what was said or done. Report internally to HR first and keep a copy of your report. If the company does not address it, file a charge with the EEOC at eeoc.gov - you have 180 days from the incident. You can also contact a private employment attorney - many take discrimination cases on contingency.";
      return "I can help you understand your employment situation. Tell me more - are you dealing with a job offer, a termination, a paycheck issue, or a workplace problem? Workers have more rights than many realize, and there is free help available for employment issues.";
    }
  },
  medicines: {
    keywords: ["medicine","medication","pill","drug","prescription","dosage","dose","side effect","pharmacy","pharmacist","label","refill","generic","brand","insurance","medicare","medicaid","cost","affordable"],
    facts: [
      "Ask your pharmacist to explain any medication - they are highly trained and consultations are free.",
      "Generic medications contain the same active ingredient as brand name drugs and are FDA-approved.",
      "GoodRx and NeedyMeds.org can significantly reduce prescription costs even without insurance.",
      "Medicare Part D covers prescription drugs - enrollment periods are specific, missing them causes penalties.",
      "Many drug manufacturers offer patient assistance programs for people who cannot afford their medications.",
      "Never stop a prescription medication abruptly without consulting a doctor - some have serious withdrawal effects.",
      "Keep a list of all medications, doses, and prescribing doctors in your wallet for emergencies.",
      "Drug interactions can be dangerous - always tell every doctor and pharmacist all medications you take.",
      "Pill organizers and phone alarms can help with complex medication schedules.",
      "You can request a 90-day supply of maintenance medications to reduce trips to the pharmacy.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("cost") || ql.includes("afford") || ql.includes("expensive") || ql.includes("insurance")) return "There are several ways to reduce medication costs: 1) Ask for the generic version - same medicine, much lower price. 2) Use GoodRx.com or the GoodRx app to compare prices at different pharmacies - it can save 80%. 3) Ask the doctor for samples. 4) Check NeedyMeds.org for patient assistance programs from drug manufacturers. 5) If you have Medicare, call 1-800-MEDICARE to review your Part D plan during open enrollment. 6) State pharmaceutical assistance programs exist in many states for seniors and low-income individuals.";
      if (ql.includes("side effect") || ql.includes("reaction") || ql.includes("feeling sick")) return "If you are experiencing side effects from a medication, do not stop taking it without first calling your doctor or pharmacist - some medications must be tapered slowly. Describe your symptoms clearly: when they started, how severe they are, and whether they are getting better or worse. Your pharmacist can tell you which side effects are common and expected versus which ones require immediate medical attention. Serious reactions like difficulty breathing, severe rash, or swelling of the face are emergencies - call 911.";
      if (ql.includes("label") || ql.includes("instructions") || ql.includes("how to take") || ql.includes("when to take")) return "Medicine labels follow a standard format: the drug name is at the top, followed by the dose (strength) like 10mg. The directions tell you how much to take, how often, and whether to take it with food. Common abbreviations: QD means once daily, BID means twice daily, TID means three times daily, PRN means as needed. Take with food means to reduce stomach upset. Avoid alcohol means alcohol can interact dangerously. If anything is unclear, call your pharmacy - they explain labels for free.";
      return "I can help you understand medication labels, instructions, or costs. I am not a doctor so for medical decisions always check with your pharmacist or healthcare provider. Tell me what medicine you are asking about and what specifically you need help understanding.";
    }
  },
  food: {
    keywords: ["food","eat","hungry","snap","ebt","food stamp","nutrition","meal","grocery","afford","feeding","pantry","wic","school lunch","free lunch"],
    facts: [
      "SNAP (food stamps) provides monthly benefits loaded onto an EBT card to buy groceries.",
      "WIC provides food benefits for pregnant women, new mothers, and children under 5.",
      "Free and reduced school lunches are available for qualifying families - apply at your school.",
      "Food banks and food pantries provide free groceries - call 211 to find one near you.",
      "Meals on Wheels provides free home-delivered meals to homebound seniors.",
      "Many restaurants offer senior discounts and some provide free meals to those in need.",
      "Community gardens often allow low-income residents to grow their own food for free.",
      "Dollar stores often have surprisingly nutritious shelf-stable food at low prices.",
      "Buying store brands instead of name brands can save 20-40% on groceries.",
      "Frozen vegetables are just as nutritious as fresh and significantly cheaper.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("snap") || ql.includes("food stamp") || ql.includes("ebt")) return "SNAP (Supplemental Nutrition Assistance Program) provides monthly benefits on an EBT card to buy groceries. To apply, go to your state's SNAP website or visit your local Department of Social Services office. You will need proof of identity, proof of income, and proof of address. Eligibility is based on household size and income. Benefits are deposited monthly and can be used at most grocery stores and some farmers markets. If approved, benefits can begin within 7-30 days. Call 211 for help applying.";
      if (ql.includes("food bank") || ql.includes("food pantry") || ql.includes("hungry") || ql.includes("cannot afford")) return "Food banks and food pantries provide free groceries with no income verification in most cases. Call 211 or text your ZIP code to 898-211 to find the nearest food pantry and their hours. Feeding America's website at feedingamerica.org also has a food bank locator. Most food banks allow you to visit once a week or month. Many also offer hot meals, diapers, and hygiene products. No one should go hungry - these programs exist exactly for this situation.";
      if (ql.includes("wic")) return "WIC (Women, Infants, and Children) provides monthly food benefits for pregnant women, new mothers up to 1 year postpartum, and children under 5. WIC provides specific foods like milk, eggs, cereal, juice, and infant formula. To apply, contact your local WIC office - find it at fns.usda.gov/wic. You will need proof of identity, proof of income, and proof of pregnancy or child's birth certificate. WIC also provides breastfeeding support and referrals to healthcare.";
      return "Food assistance is available and there is no shame in using it. Tell me more about your situation - are you looking for emergency food today, help with grocery costs long-term, or information about a specific program? I can point you to the right resources.";
    }
  },
  appointments: {
    keywords: ["appointment","doctor","meeting","court","school","interview","prepare","upcoming","schedule","remind","bring","what to expect"],
    facts: [
      "Write down all your questions before any appointment - you will likely forget them once you are there.",
      "Bring a list of all current medications to every medical appointment.",
      "You have the right to bring a support person to any medical or legal appointment.",
      "Ask for an interpreter if English is not your first language - it is your right in medical and legal settings.",
      "Take notes during appointments or ask if you can record the conversation.",
      "If you cannot make an appointment, call as early as possible - last-minute no-shows can affect your care.",
      "Ask the doctor to explain things in plain language if you do not understand.",
      "For court hearings, dress professionally and arrive at least 30 minutes early.",
      "Medicaid and Medicare cover preventive care appointments at no cost.",
      "Community health centers provide care on a sliding fee scale based on income.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("doctor") || ql.includes("medical") || ql.includes("health")) return "To prepare for a medical appointment: write down your symptoms with when they started and how severe, list all your current medications and supplements, write down any questions you want answered, and bring your insurance card and ID. At the appointment, do not be afraid to say 'I do not understand, can you explain that differently?' You have the right to ask for everything in writing. Ask specifically: What is the diagnosis? What are my options? What happens if I do not treat it? What are the side effects of the medication?";
      if (ql.includes("court") || ql.includes("hearing") || ql.includes("judge")) return "For a court hearing, preparation is critical. Arrive at least 30 minutes early to clear security and find the right courtroom. Dress professionally - business casual at minimum. Bring: all relevant documents organized in a folder, any evidence like photos or receipts, contact information for witnesses, and a notepad and pen. Address the judge as 'Your Honor.' Speak only when asked. Turn your phone completely off. If you have an attorney, let them speak for you. If you are representing yourself, be brief and stick to facts.";
      if (ql.includes("interview") || ql.includes("job")) return "For a job interview, prepare by researching the company online before you go. Bring several copies of your resume and a list of references. Dress one level above what employees typically wear. Arrive 10-15 minutes early. Common questions to prepare for: Tell me about yourself (keep it professional and brief), What are your strengths and weaknesses, Why do you want this job, and Tell me about a challenge you overcame. At the end, always ask questions - good ones include: What does success look like in this role? What are the next steps?";
      return "I can help you prepare for your appointment. Tell me what kind of appointment it is and when it is. I will help you know what to bring, what to expect, and what questions to ask so you feel confident and ready.";
    }
  },
  emergency: {
    keywords: ["emergency","danger","911","hurt","injury","violence","domestic","abuse","crisis","suicide","mental health","988","poison","overdose","fire","flood","disaster","safe","unsafe"],
    facts: [
      "Call 911 for any immediate danger to life - police, fire, or medical emergency.",
      "988 is the Suicide and Crisis Lifeline - call or text 24 hours a day.",
      "1-800-799-7233 is the National Domestic Violence Hotline - available 24/7.",
      "1-800-222-1222 is Poison Control - call immediately for any poisoning emergency.",
      "211 connects you to local emergency social services, food, shelter, and crisis help.",
      "Text HOME to 741741 to reach the Crisis Text Line if you cannot speak safely.",
      "FEMA disaster assistance is available after declared disasters at disasterassistance.gov.",
      "Emergency rooms cannot turn you away for inability to pay under EMTALA law.",
      "Safe shelter from domestic violence is available in every state - call 211 for your local shelter.",
      "If you smell gas, leave immediately and call 911 - do not use any electrical switches.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("suicid") || ql.includes("kill myself") || ql.includes("want to die") || ql.includes("end my life")) return "I am concerned about you. Please call or text 988 right now - that is the Suicide and Crisis Lifeline, available 24 hours a day. You can also text HOME to 741741 if you cannot talk safely. If you are in immediate danger, call 911. You do not have to face this alone, and there are people who want to help you through this moment. Please reach out to 988 now.";
      if (ql.includes("domestic") || ql.includes("abuse") || ql.includes("violence") || ql.includes("hurt me") || ql.includes("hitting")) return "Your safety is the most important thing. The National Domestic Violence Hotline is 1-800-799-7233, available 24 hours a day. You can also text START to 88788 or chat at thehotline.org if it is not safe to call. If you are in immediate danger, call 911. Local domestic violence shelters provide safe housing, legal advocacy, and support - call 211 to find your nearest shelter. You deserve to be safe.";
      if (ql.includes("poison") || ql.includes("overdose") || ql.includes("swallowed") || ql.includes("ate")) return "Call Poison Control immediately at 1-800-222-1222. They are available 24 hours a day and will tell you exactly what to do. If the person is unconscious, not breathing, or having a seizure, call 911 first. When you call, tell them: what was taken, how much, when it was taken, and the person's age and weight. Do not make the person vomit unless Poison Control specifically tells you to.";
      return "If you are in immediate danger, call 911 now. For crisis support: 988 for suicide or mental health crisis, 1-800-799-7233 for domestic violence, 1-800-222-1222 for poison, and 211 for local emergency resources. Tell me what is happening and I will help you find the right help.";
    }
  },
  credit: {
    keywords: ["credit","score","credit score","report","fico","equifax","experian","transunion","credit card","debt","loan","interest","apr","collection","derogatory","dispute","improve credit","build credit"],
    facts: [
      "You can get a free credit report from all three bureaus once a year at annualcreditreport.com.",
      "Paying bills on time is the single most important factor in your credit score - it is 35% of your FICO score.",
      "Keeping credit card balances below 30% of your limit improves your score.",
      "Checking your own credit (soft inquiry) does not hurt your score.",
      "Negative items like late payments stay on your credit report for 7 years.",
      "Bankruptcy stays on your credit for 7-10 years depending on the type.",
      "You can dispute errors on your credit report for free at each bureau's website.",
      "Secured credit cards can help you build credit when you have none or poor credit.",
      "Becoming an authorized user on someone else's card can help build your credit.",
      "Credit repair companies cannot do anything you cannot do yourself for free.",
    ],
    response: (q) => {
      const ql = q.toLowerCase();
      if (ql.includes("dispute") || ql.includes("error") || ql.includes("wrong") || ql.includes("incorrect")) return "You have the legal right to dispute any error on your credit report for free. Get your free reports at annualcreditreport.com. For each error, file a dispute directly with the bureau (Equifax, Experian, or TransUnion) online, by mail, or by phone. The bureau must investigate within 30 days and correct or remove any information they cannot verify. Send disputes by certified mail if possible and keep copies. The FTC has a sample dispute letter at consumer.ftc.gov. You do not need a credit repair company - this is completely free to do yourself.";
      if (ql.includes("improve") || ql.includes("build") || ql.includes("raise") || ql.includes("better")) return "The most effective ways to improve your credit score: 1) Pay every bill on time - set up autopay for minimums. 2) Keep credit card balances below 30% of your limit. 3) Do not close old credit cards - length of credit history matters. 4) Limit new credit applications - each hard inquiry slightly lowers your score. 5) Check your credit report for errors and dispute them. Secured credit cards and credit builder loans from credit unions are good tools if you are starting from scratch. Most people see improvement within 3-6 months of consistent good habits.";
      return "Tell me more about your credit situation - are you trying to understand your score, dispute something on your report, or figure out how to improve your credit? Everyone deserves access to affordable credit and I can walk you through your options.";
    }
  },
};

// ---------------------------------------------------------------------------
// Smart fallback - searches KB then responds contextually
// ---------------------------------------------------------------------------
function getSmartFallback(question) {
  const q = (question || "").toLowerCase();

  // Find best matching category by keyword count
  let bestCategory = null;
  let bestScore = 0;
  for (const [cat, data] of Object.entries(KB)) {
    const score = data.keywords.filter(kw => q.includes(kw)).length;
    if (score > bestScore) { bestScore = score; bestCategory = cat; }
  }

  if (bestCategory && bestScore > 0) {
    return KB[bestCategory].response(question);
  }

  // Generic helpful response
  return "I want to help you with that. Can you tell me a little more - like who sent the document, what it says, or what specifically is confusing? The more you share, the better I can explain things in plain words. You can also choose a topic button above to get started on a specific area.";
}

// ---------------------------------------------------------------------------
// API hook - backend first, then Anthropic direct, then KB fallback
// ---------------------------------------------------------------------------
function useHelperAPI() {
  return useCallback(async (question, topicKey) => {
    const token = localStorage.getItem("lce_token");

    // 1. Try backend /api/ai/chat (logged-in users)
    if (token) {
      try {
        const systemContext = topicKey && KB[topicKey]
          ? "You are a plain-language helper. Additional knowledge context: " + KB[topicKey].facts.join(" ")
          : "You are a plain-language helper for WAI-Institute.";
        const r = await fetch("/api/ai/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
          body: JSON.stringify({ session_id: "helper-" + Date.now(), message: question, mode: "tutor" }),
        });
        if (r.ok) {
          const data = await r.json();
          if (data.reply) return data.reply;
        }
      } catch {}
    }

    // 2. Try Anthropic API directly with KB context
    try {
      const kbContext = topicKey && KB[topicKey]
        ? "\n\nRelevant knowledge for this topic:\n" + KB[topicKey].facts.map(f => "- " + f).join("\n")
        : "";
      const r = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 350,
          messages: [{ role: "user", content: question }],
          system: "You are a warm, plain-language helper for WAI-Institute. Help people understand mail, bills, legal papers, housing, employment, medicines, food assistance, and daily life challenges. Keep answers to 3-5 sentences, warm, and use simple words. Never use jargon. Include specific actionable steps when possible. If someone asks about an emergency say call 911. If legal say seek free legal aid. If medical say see a doctor." + kbContext,
        }),
      });
      if (r.ok) {
        const data = await r.json();
        const reply = data.content?.find(b => b.type === "text")?.text;
        if (reply) return reply;
      }
    } catch {}

    // 3. KB-powered smart fallback
    return getSmartFallback(question);
  }, []);
}

// ---------------------------------------------------------------------------
// Mic hook
// ---------------------------------------------------------------------------
function useMic({ onResult, onError }) {
  const [listening, setListening] = useState(false);
  const recogRef = useRef(null);

  const start = useCallback(async () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { onError("Voice input is not supported in this browser. Please use Chrome or Edge."); return; }
    try { await navigator.mediaDevices.getUserMedia({ audio: true }); }
    catch { onError("Microphone access was denied. Please allow mic access in your browser settings."); return; }
    const rec = new SR();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onstart = () => setListening(true);
    rec.onend = () => setListening(false);
    rec.onresult = (e) => { const t = e.results[0]?.[0]?.transcript || ""; if (t.trim()) onResult(t.trim()); };
    rec.onerror = (e) => {
      setListening(false);
      if (e.error === "not-allowed") onError("Microphone access denied. Please allow mic access and try again.");
      else if (e.error === "no-speech") onError("No speech detected. Please try again.");
      else onError("Microphone error: " + e.error);
    };
    recogRef.current = rec;
    rec.start();
  }, [onResult, onError]);

  const stop = useCallback(() => { recogRef.current?.stop(); setListening(false); }, []);
  const toggle = useCallback(() => { if (listening) stop(); else start(); }, [listening, start, stop]);
  return { listening, toggle };
}

// ---------------------------------------------------------------------------
// TTS hook - nova for public, shimmer for auth
// ---------------------------------------------------------------------------
function useTTS(voice) {
  const [speaking, setSpeaking] = useState(false);
  const audioRef = useRef(null);
  const abortRef = useRef(null);

  const speakBrowser = useCallback((text) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = "en-US"; utt.rate = 0.88; utt.pitch = 1.05;
    const voices = window.speechSynthesis.getVoices();
    const female = voices.find(v =>
      v.lang.startsWith("en") && (v.name.includes("Samantha") || v.name.includes("Karen") ||
      v.name.includes("Victoria") || v.name.includes("Zira") || v.name.toLowerCase().includes("female"))
    );
    if (female) utt.voice = female;
    utt.onstart = () => setSpeaking(true);
    utt.onend = () => setSpeaking(false);
    utt.onerror = () => setSpeaking(false);
    window.speechSynthesis.speak(utt);
  }, []);

  const speak = useCallback(async (text) => {
    if (!text) return;
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis?.cancel();
    const token = localStorage.getItem("lce_token");
    if (!token) { speakBrowser(text); return; }
    const controller = new AbortController();
    abortRef.current = controller;
    setSpeaking(true);
    try {
      const r = await fetch("/api/ai/sage/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ text: text.slice(0, 1000), voice: voice || "nova", speed: 0.95, session_id: "helper-tts" }),
        signal: controller.signal,
      });
      if (!r.ok) { setSpeaking(false); speakBrowser(text); return; }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => { URL.revokeObjectURL(url); setSpeaking(false); };
      audio.onpause = () => setSpeaking(false);
      audio.onerror = () => { setSpeaking(false); speakBrowser(text); };
      audio.play();
    } catch (e) {
      if (e?.name !== "AbortError") { setSpeaking(false); speakBrowser(text); }
    }
  }, [voice, speakBrowser]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }, []);

  return { speaking, speak, stop };
}

// Mobile keyboard fix
function useMobileKeyboardFix(endRef) {
  useEffect(() => {
    const vv = window.visualViewport;
    if (!vv) return;
    const handler = () => {
      if (endRef.current) endRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    };
    vv.addEventListener("resize", handler);
    vv.addEventListener("scroll", handler);
    return () => { vv.removeEventListener("resize", handler); vv.removeEventListener("scroll", handler); };
  }, [endRef]);
}

// ---------------------------------------------------------------------------
// PUBLIC HELPER
// ---------------------------------------------------------------------------
function PublicHelper() {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [name, setName] = useState("Friend");
  const [nameInput, setNameInput] = useState("");
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [activeTopic, setActiveTopic] = useState(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI();
  const navigate = useNavigate();
  const { speaking, speak, stop: stopSpeech } = useTTS("nova");
  useMobileKeyboardFix(endRef);

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  }, []);

  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);
    const reply = await callAPI(text, topicKey || activeTopic);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    inputRef.current?.focus();
  }, [loading, callAPI, addMsg, audioEnabled, speak, activeTopic]);

  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    inputRef.current?.focus();
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => sendText(t, activeTopic),
    onError: (msg) => showToast(msg),
  });

  useEffect(() => {
    addMsg("helper", "Hello! I am here to help you understand mail, bills, legal papers, housing, medicines, and more - all in plain, simple words. Choose a topic below or just type your question.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs]);

  const TOPICS = [
    { key:"mail", icon:"📬", title:"Understand a Letter", prompt:"I can help you understand any letter or official document. Please type or paste what it says - or tell me who sent it - and I will explain what it means and what you need to do." },
    { key:"bills", icon:"💡", title:"Explain My Bill", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says. I will explain each part clearly." },
    { key:"credit", icon:"💳", title:"Credit Score", prompt:"I can explain your credit score and what affects it. What would you like to know?" },
    { key:"custody", icon:"👶", title:"Custody Help", prompt:"I can help you understand custody papers. Please type the key parts of the document." },
    { key:"medicines", icon:"💊", title:"My Medicines", prompt:"I can help you read medicine labels and understand instructions. What medicine do you need help with?" },
    { key:"food", icon:"🍽️", title:"Food Assistance", prompt:"I can help with food assistance programs or nutrition questions. What do you need?" },
    { key:"appointments", icon:"📅", title:"Appointments", prompt:"I can help you prepare for an appointment. What kind is it and when is it?" },
    { key:"legal", icon:"⚖️", title:"Legal Help", prompt:"I can help explain legal papers in simple words. Please type or paste the key parts." },
    { key:"employment", icon:"💼", title:"Employment Help", prompt:"I can help you understand job papers or employment situations. What do you have?" },
    { key:"housing", icon:"🏠", title:"Housing", prompt:"I can help with rent, lease, eviction notices, and housing letters. Please tell me what the document says." },
    { key:"scam", icon:"🛡️", title:"Check for Scams", prompt:"I can check something for scam signs. Paste or type what you received and I will tell you what I see." },
    { key:"emergency", icon:"🚨", title:"Emergency Numbers", prompt:"Emergency: 911 for danger. 988 for mental health crisis. 1-800-222-1222 for Poison Control. Are you safe right now?" },
  ];

  const activeTitle = TOPICS.find(t => t.key === activeTopic)?.title;

  const S = {
    wrap: { display:"flex", flexDirection:"column", height:"100dvh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933", overflow:"hidden" },
    header: { background:"linear-gradient(135deg,#4b7cff,#7b5cff)", padding:"12px 16px", flexShrink:0 },
    scrollArea: { flex:1, overflowY:"auto", padding:"0 10px 8px", WebkitOverflowScrolling:"touch" },
    card: { background:"#fff", borderRadius:14, padding:"12px", margin:"10px 0", boxShadow:"0 2px 12px rgba(15,23,42,.08)" },
    bubble: (role) => ({ maxWidth:"88%", background:role==="helper"?"#dbeafe":"#f3f4f6", borderRadius:14, padding:"10px 12px", fontSize:14, lineHeight:1.55, alignSelf:role==="helper"?"flex-start":"flex-end" }),
    // INPUT ROW — mic, audio toggle, textarea, send all in one row
    inputRow: { display:"flex", gap:6, alignItems:"flex-end", padding:"8px 10px", background:"#fff", borderTop:"1px solid #e5e7eb", flexShrink:0 },
    textarea: { flex:1, minHeight:44, maxHeight:100, resize:"none", borderRadius:12, border:"1px solid #d1d5db", padding:"10px 12px", fontSize:15, fontFamily:"system-ui", outline:"none", lineHeight:1.4 },
    sendBtn: { borderRadius:12, border:"none", padding:"12px 14px", fontSize:14, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer", flexShrink:0 },
    iconBtn: (active, color) => ({ borderRadius:12, border:"none", padding:"12px 12px", fontSize:18, background:active?color:"#f3f4f6", color:active?"#fff":"#374151", cursor:"pointer", flexShrink:0 }),
    toast: { position:"fixed", top:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, whiteSpace:"nowrap", boxShadow:"0 4px 20px rgba(0,0,0,.3)" },
  };

  return (
    <div style={S.wrap}>
      {/* HEADER */}
      <div style={S.header}>
        <div style={{ display:"flex", alignItems:"center", gap:12, color:"#fff" }}>
          <div style={{ width:48, height:48, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:22, flexShrink:0 }}>H</div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:18, fontWeight:700 }}>W.A.I. Help Center</div>
            <div style={{ fontSize:12, opacity:0.9 }}>Plain-language help for mail, bills, legal papers, housing and more</div>
          </div>
          <button onClick={() => navigate("/login")} style={{ borderRadius:999, border:"1px solid rgba(255,255,255,.7)", padding:"8px 14px", fontSize:13, background:"transparent", color:"#fff", cursor:"pointer", fontWeight:600 }}>Sign in</button>
        </div>
        <div style={{ display:"flex", gap:8, alignItems:"center", marginTop:10, flexWrap:"wrap", color:"#fff" }}>
          <span style={{ fontSize:14, fontWeight:600 }}>Hello, {name}!</span>
          <input value={nameInput} onChange={e => setNameInput(e.target.value)}
            onKeyDown={e => { if (e.key==="Enter" && nameInput.trim()) { setName(nameInput.trim()); setNameInput(""); }}}
            placeholder="Tell me your name..." style={{ padding:"5px 10px", borderRadius:999, border:"none", fontSize:13, width:150, background:"rgba(255,255,255,.2)", color:"#fff", outline:"none" }} />
          {nameInput.trim() && (
            <button onClick={() => { setName(nameInput.trim()); setNameInput(""); }} style={{ borderRadius:999, border:"none", padding:"5px 10px", fontSize:12, background:"#22c55e", color:"#064e3b", cursor:"pointer", fontWeight:600 }}>Save</button>
          )}
        </div>
      </div>

      {/* SCROLLABLE CONTENT */}
      <div style={S.scrollArea}>
        <div style={S.card}>
          <div style={{ fontSize:13, fontWeight:700, color:"#374151", marginBottom:8 }}>
            {activeTopic ? "Topic: " + activeTitle + " - tap another to switch" : "Choose a topic or type your question below"}
          </div>
          <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(130px,1fr))", gap:8 }}>
            {TOPICS.map(({ key, icon, title, prompt }) => (
              <button key={key} onClick={() => startTopic(key, title, prompt)}
                style={{ borderRadius:10, border:"2px solid " + (activeTopic===key?"#2563eb":"#e5e7eb"), background:activeTopic===key?"#eff6ff":"#f9fafb", padding:"10px 8px", cursor:"pointer", display:"flex", flexDirection:"column", gap:4, textAlign:"left" }}>
                <span style={{ fontSize:20 }}>{icon}</span>
                <span style={{ fontSize:12, fontWeight:600 }}>{title}</span>
              </button>
            ))}
          </div>
        </div>

        <div style={S.card}>
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {msgs.map((m, i) => (
              <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="helper"?"flex-start":"flex-end" }}>
                <div style={S.bubble(m.role)}>
                  {m.text}
                  {m.role==="helper" && (
                    <button onClick={() => speak(m.text)} title="Read aloud"
                      style={{ background:"none", border:"none", cursor:"pointer", fontSize:14, opacity:0.5, marginLeft:6, padding:0, verticalAlign:"middle" }}>🔊</button>
                  )}
                </div>
                <div style={{ fontSize:11, color:"#9ca3af", marginTop:2, marginLeft:4, marginRight:4 }}>
                  {m.role==="helper" ? "Helper" : name} - {m.time}
                </div>
              </div>
            ))}
            {loading && <div style={{ color:"#6b7280", fontSize:13, fontStyle:"italic" }}>Helper is thinking...</div>}
            <div ref={endRef} style={{ height:1 }} />
          </div>
          <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:10 }}>
            <button onClick={() => { setMsgs([]); setActiveTopic(null); addMsg("helper","Back to the start. Choose a topic or type your question."); }}
              style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>Start over</button>
            <button onClick={() => sendText("Is this a scam? Help me check.", "scam")}
              style={{ borderRadius:999, border:"1px solid #fecaca", padding:"6px 12px", fontSize:12, background:"#fef2f2", color:"#b91c1c", cursor:"pointer" }}>Scam check</button>
            {speaking && <button onClick={stopSpeech} style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>Stop audio</button>}
          </div>
          <div style={{ marginTop:10, fontSize:11, color:"#9ca3af", textAlign:"center" }}>
            Public helper - no data saved.{" "}
            <button onClick={() => navigate("/login")} style={{ background:"none", border:"none", color:"#2563eb", cursor:"pointer", fontSize:11, padding:0 }}>Sign in</button> for saved notes and more tools.
          </div>
        </div>
        <div style={{ height:20 }} />
      </div>

      {/* INPUT ROW - mic, audio toggle, textarea, send all together */}
      <div style={S.inputRow}>
        <button onClick={toggleMic} style={S.iconBtn(listening, "#dc2626")} title={listening?"Stop":"Speak"}>
          {listening ? "🔴" : "🎙️"}
        </button>
        <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }}
          style={S.iconBtn(audioEnabled, "#059669")} title={audioEnabled?"Audio ON - tap to turn off":"Audio OFF - tap to turn on"}>
          {audioEnabled ? "🔊" : "🔇"}
        </button>
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); sendText(input, activeTopic); }}}
          onFocus={() => setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 300)}
          placeholder={listening ? "Listening... speak now" : activeTopic ? "Ask about " + activeTitle + "..." : "Type your question here..."}
          style={S.textarea}
          rows={1}
        />
        <button onClick={() => sendText(input, activeTopic)} disabled={loading} style={S.sendBtn}>Send</button>
      </div>

      {toast && <div style={S.toast}>{toast}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AUTH HELPER
// ---------------------------------------------------------------------------
function AuthHelper({ user }) {
  const [msgs, setMsgs] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
  const [activeNav, setActiveNav] = useState("home");
  const [audioEnabled, setAudioEnabled] = useState(false);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const callAPI = useHelperAPI();
  const { speaking, speak, stop: stopSpeech } = useTTS("shimmer");
  useMobileKeyboardFix(endRef);

  const showToast = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
  }, []);

  const addMsg = useCallback((role, text) => {
    const time = new Date().toLocaleTimeString([], { hour:"numeric", minute:"2-digit" });
    setMsgs(m => [...m, { role, text, time }]);
  }, []);

  const sendText = useCallback(async (text, topicKey) => {
    if (!text.trim() || loading) return;
    addMsg("user", text);
    setInput("");
    setLoading(true);
    const reply = await callAPI(text, topicKey || activeTopic);
    addMsg("helper", reply);
    if (audioEnabled) speak(reply);
    setLoading(false);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    inputRef.current?.focus();
  }, [loading, callAPI, addMsg, audioEnabled, speak, activeTopic]);

  const startTopic = useCallback((topicKey, title, prompt) => {
    setActiveTopic(topicKey);
    addMsg("helper", prompt);
    if (audioEnabled) speak(prompt);
    setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 100);
    inputRef.current?.focus();
  }, [addMsg, audioEnabled, speak]);

  const { listening, toggle: toggleMic } = useMic({
    onResult: (t) => sendText(t, activeTopic),
    onError: (msg) => showToast(msg),
  });

  useEffect(() => {
    addMsg("helper", "Welcome back, " + (user?.full_name?.split(" ")[0] || "there") + ". I am your private helper inside WAI-Institute. Choose a topic or type your question. I will keep answers short and clear.");
  }, []);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [msgs]);

  const AUTH_TOOLS = [
    { section:"Daily tools", items:[
      { key:"mail", icon:"📬", title:"Understand a letter", prompt:"I can help you understand your mail. Paste or type what the letter says and I will explain what it means and what you need to do." },
      { key:"bills", icon:"💡", title:"Explain my bill", prompt:"I can help with your bills. Tell me who sent it, the amount, and what it says. I will break it down clearly." },
      { key:"appointments", icon:"📅", title:"Appointments", prompt:"I can help you prepare for an upcoming appointment. What kind is it and when is it?" },
      { key:"notes", icon:"📝", title:"Notes", prompt:"I can help you keep simple notes or reminders. What would you like to write down?" },
      { key:"documents", icon:"🗂️", title:"Documents", prompt:"I can help you find or understand documents. What are you looking for?" },
    ]},
    { section:"Legal tools", items:[
      { key:"legal-draft", icon:"📄", title:"Help draft a form", prompt:"I can help you draft a simple legal form in plain language. What type of form and what is the situation?" },
      { key:"letter-draft", icon:"✉️", title:"Help write a letter", prompt:"I can help you write a clear, respectful letter. Who is it to and what do you need to say?" },
      { key:"legal", icon:"⚖️", title:"Explain legal papers", prompt:"I can explain legal documents in plain words. Paste or type the key parts and I will walk you through them." },
      { key:"scam", icon:"🛡️", title:"Scam check", prompt:"I can check for scam signs. Paste the message, email, or letter you received and I will flag anything suspicious." },
    ]},
    { section:"Health and life", items:[
      { key:"medicines", icon:"💊", title:"Understand medicines", prompt:"I can help you understand medicine labels and instructions. What is the medicine and what does the label say?" },
      { key:"food", icon:"🍽️", title:"Food assistance", prompt:"I can give simple food guidance or help with food assistance programs. What do you need?" },
      { key:"housing", icon:"🏠", title:"Housing", prompt:"I can help with housing documents. Do you have a lease, eviction notice, rent increase letter, or something else?" },
      { key:"employment", icon:"💼", title:"Employment", prompt:"I can help with job papers and employment situations. What type of document or situation do you have?" },
    ]},
    { section:"Support", items:[
      { key:"trusted-contacts", icon:"📇", title:"Trusted contacts", prompt:"I can help you review or update your trusted contacts. What would you like to do?" },
      { key:"caregiver-mode", icon:"❤️", title:"Caregiver mode", prompt:"Caregiver mode lets a trusted person work alongside you. Is a caregiver present with you right now?" },
      { key:"emergency", icon:"🚨", title:"Emergency Numbers", prompt:"Emergency: 911 for immediate danger. 988 for mental health crisis. 1-800-222-1222 for Poison Control. Are you safe right now?" },
    ]},
  ];

  const activeTopicTitle = AUTH_TOOLS.flatMap(s => s.items).find(t => t.key === activeTopic)?.title;

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const S = {
    wrap: { display:"flex", flexDirection:"column", height:"100dvh", background:"#f5f7fb", fontFamily:"system-ui,-apple-system,sans-serif", color:"#1f2933", overflow:"hidden" },
    topBar: { background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"10px 14px", display:"flex", alignItems:"center", justifyContent:"space-between", gap:10, flexWrap:"wrap", flexShrink:0 },
    body: { display:"flex", flex:1, overflow:"hidden" },
    sidebar: { width:sidebarOpen?220:0, flexShrink:0, overflowY:"auto", overflowX:"hidden", borderRight:sidebarOpen?"1px solid #e5e7eb":"none", background:"#fff", WebkitOverflowScrolling:"touch", transition:"width 0.2s", padding:sidebarOpen?"10px 8px":0 },
    main: { flex:1, display:"flex", flexDirection:"column", overflow:"hidden" },
    msgArea: { flex:1, overflowY:"auto", padding:"10px 16px", WebkitOverflowScrolling:"touch" },
    toolBtn: (active) => ({ borderRadius:10, border:"2px solid " + (active?"#2563eb":"#e5e7eb"), background:active?"#eff6ff":"#f9fafb", padding:"8px 10px", cursor:"pointer", display:"flex", alignItems:"center", gap:8, fontSize:13, fontWeight:active?700:400, width:"100%", textAlign:"left", marginBottom:4 }),
    bubble: (role) => ({ maxWidth:"85%", background:role==="helper"?"#dbeafe":"#f3f4f6", borderRadius:14, padding:"10px 14px", fontSize:15, lineHeight:1.6, alignSelf:role==="helper"?"flex-start":"flex-end" }),
    inputRow: { display:"flex", gap:6, alignItems:"flex-end", padding:"8px 16px", background:"#fff", borderTop:"1px solid #e5e7eb", flexShrink:0 },
    textarea: { flex:1, minHeight:48, maxHeight:120, resize:"none", borderRadius:12, border:"1px solid #d1d5db", padding:"12px 14px", fontSize:15, fontFamily:"system-ui", outline:"none" },
    sendBtn: { borderRadius:12, border:"none", padding:"14px 18px", fontSize:15, fontWeight:700, background:"#2563eb", color:"#fff", cursor:"pointer", flexShrink:0 },
    iconBtn: (active, color) => ({ borderRadius:12, border:"none", padding:"12px 12px", fontSize:18, background:active?color:"#f3f4f6", color:active?"#fff":"#374151", cursor:"pointer", flexShrink:0 }),
    navPill: (active) => ({ borderRadius:999, padding:"5px 10px", fontSize:12, border:"1px solid " + (active?"#2563eb":"#d1d5db"), background:active?"#2563eb":"#fff", color:active?"#fff":"#111827", cursor:"pointer", fontWeight:active?600:400 }),
    toast: { position:"fixed", top:16, left:"50%", transform:"translateX(-50%)", background:"#111827", color:"#f9fafb", padding:"10px 18px", borderRadius:999, fontSize:13, zIndex:9999, whiteSpace:"nowrap", boxShadow:"0 4px 20px rgba(0,0,0,.3)" },
  };

  return (
    <div style={S.wrap}>
      <div style={S.topBar}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <button onClick={() => setSidebarOpen(o => !o)}
            style={{ borderRadius:10, border:"1px solid #e5e7eb", padding:"8px 10px", background:sidebarOpen?"#eff6ff":"#f9fafb", cursor:"pointer", fontSize:13, fontWeight:600, color:sidebarOpen?"#2563eb":"#374151", flexShrink:0 }}>
            {sidebarOpen ? "Hide Tools" : "Show Tools"}
          </button>
          <div style={{ width:32, height:32, borderRadius:"50%", background:"radial-gradient(circle at 30% 20%,#fde68a,#facc15 40%,#f97316 80%)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:16 }}>H</div>
          <div>
            <div style={{ fontSize:14, fontWeight:700 }}>Helper Workspace</div>
            <div style={{ fontSize:11, color:"#6b7280" }}>{user?.full_name || "WAI-Institute"}</div>
          </div>
        </div>
        <div style={{ display:"flex", gap:6, alignItems:"center", flexWrap:"wrap" }}>
          {activeTopic && (
            <span style={{ borderRadius:999, padding:"5px 10px", fontSize:12, background:"#eff6ff", color:"#1d4ed8", border:"1px solid #bfdbfe", fontWeight:600 }}>
              {activeTopicTitle}
            </span>
          )}
          <span style={{ borderRadius:999, padding:"5px 10px", fontSize:11, border:"1px solid #d1d5db", background:"#f9fafb" }}>{user?.role||"Student"}</span>
        </div>
      </div>

      <div style={S.body}>
        <div style={S.sidebar}>
          {sidebarOpen && AUTH_TOOLS.map(({ section, items }) => (
            <div key={section} style={{ marginBottom:16 }}>
              <div style={{ fontSize:11, fontWeight:700, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.05em", marginBottom:6 }}>{section}</div>
              {items.map(({ key, icon, title, prompt }) => (
                <button key={key} style={S.toolBtn(activeTopic===key)} onClick={() => { startTopic(key, title, prompt); setSidebarOpen(false); }}>
                  <span style={{ fontSize:16 }}>{icon}</span><span>{title}</span>
                </button>
              ))}
            </div>
          ))}
        </div>

        <div style={S.main}>


          <div style={S.msgArea}>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {msgs.map((m, i) => (
                <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:m.role==="helper"?"flex-start":"flex-end" }}>
                  <div style={S.bubble(m.role)}>
                    {m.text}
                    {m.role==="helper" && (
                      <button onClick={() => speak(m.text)} title="Read aloud"
                        style={{ background:"none", border:"none", cursor:"pointer", fontSize:14, opacity:0.5, marginLeft:6, padding:0, verticalAlign:"middle" }}>🔊</button>
                    )}
                  </div>
                  <div style={{ fontSize:11, color:"#9ca3af", marginTop:2, marginLeft:4, marginRight:4 }}>
                    {m.role==="helper"?"Helper":"You"} - {m.time}
                  </div>
                </div>
              ))}
              {loading && <div style={{ color:"#6b7280", fontSize:13, fontStyle:"italic" }}>Helper is thinking...</div>}
              <div ref={endRef} style={{ height:1 }} />
            </div>
            <div style={{ display:"flex", flexWrap:"wrap", gap:6, marginTop:12 }}>
              <button onClick={() => { setMsgs([]); setActiveTopic(null); addMsg("helper","Cleared. Choose a tool or type your question."); }}
                style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>Clear chat</button>
              {speaking && <button onClick={stopSpeech} style={{ borderRadius:999, border:"1px solid #d1d5db", padding:"6px 12px", fontSize:12, background:"#fff", cursor:"pointer" }}>Stop audio</button>}
            </div>
            <div style={{ marginTop:10, fontSize:11, color:"#9ca3af", textAlign:"center" }}>
              This helper is part of WAI-Institute. Actions may be logged for safety and training.
            </div>
          </div>

          <div style={S.inputRow}>
            <button onClick={toggleMic} style={S.iconBtn(listening, "#dc2626")} title={listening?"Stop":"Speak"}>
              {listening ? "🔴" : "🎙️"}
            </button>
            <button onClick={() => { setAudioEnabled(a => !a); if (speaking) stopSpeech(); }}
              style={S.iconBtn(audioEnabled, "#059669")} title={audioEnabled?"Audio ON":"Audio OFF"}>
              {audioEnabled ? "🔊" : "🔇"}
            </button>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key==="Enter" && !e.shiftKey) { e.preventDefault(); sendText(input, activeTopic); }}}
              onFocus={() => setTimeout(() => endRef.current?.scrollIntoView({ behavior:"smooth" }), 300)}
              placeholder={listening ? "Listening..." : activeTopic ? "Ask about " + activeTopicTitle + "..." : "Type your question..."}
              style={S.textarea}
            />
            <button onClick={() => sendText(input, activeTopic)} disabled={loading} style={S.sendBtn}>Send</button>
          </div>
        </div>
      </div>

      {toast && <div style={S.toast}>{toast}</div>}
    </div>
  );
}
