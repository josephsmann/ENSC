
url = ""
with open("ENSC_url.txt") as fn:
    summermembership_url = fn.readline().strip()
    summerclass_url = fn.readline().strip()
    print(summermembership_url)
    print(summerclass_url)

import pandas as pd
from datetime import timedelta

# skipfooter because last line is a summary
df = pd.read_csv(summermembership_url, sep='\t', parse_dates=[
                 'Created', 'Birth Date'], skipfooter=1, engine='python')

# clean up column names
_d = {c: c.replace(' ', '_').replace('.', '_') for c in df.columns}
df.rename(columns=_d, inplace=True)

cart_cols = ['Created', 'SubTotal', 'OnlineRegFee',
             'CartTotal',  'CreditCardName', 'RemittanceID', 'MembershipType', 'MembershipType_1', 'z4_fee', 'GroomingDonateD', 'ccc_fee_cart', 'ENSC_subtotal', 'Credit_fees', 'ENSC_OnlineRegFee', 'ENSC_total']

ind_cols = ['First_Name',
            'LastName', 'Address', 'City', 'Province',
            'Postal/Zip_Code', 'Country', 'Cell_Phone', 'Email', 'Birth_Date',
            'Gender', 'Ind_MembershipType', 'Ind_MembershipType_1'
            'CCC_Membership_Status', 'CCC_Membership']

year_start = pd.to_datetime('July 1, 2017')

df.loc[:, "age"] = ((year_start - df.Birth_Date) /
                    timedelta(days=365.25)).astype(int)


def age_cat(age):
    if age < 13:
        return 0
    if age < 19:
        return 1
    return 2


df.loc[:, "age_cat"] = df.age.apply(age_cat)


def ccc_fee(r):
    if r.CCC_Membership_Status == "Regular Club Member":
        if r.age_cat == 0:
            return 11
        if r.age_cat == 1:
            return 13
        if r.age_cat == 2:
            return 18
    else:
        return 0


df.loc[:, 'ccc_fee'] = df.apply(ccc_fee, axis=1)

# total fee is Membership fee from Cart page plus ccc_fees from ind pages
# + plus zone 4 fees + credit fees
_df = (df.groupby('Cart')['ccc_fee'].sum())
# df.loc[:,'cart_ccc_fee'] =
df1 = df.set_index('Cart').join(_df, rsuffix='_cart')


z4_s = df.groupby('Cart')['Cart'].count() + 1
df2 = df1.join(z4_s, rsuffix='_cart')
df2.rename(columns={'Cart': 'z4_fee'}, inplace=True)
# df.set_index('Cart')

df2.loc[:, 'GroomingDonateD'] = df2.GroomingDonate.str.extract(
    '(\d+)', expand=False).astype(float).fillna(0)

df2.loc[:, 'ENSC_subtotal'] = df2.ccc_fee_cart + \
    df2.MembershipType_1 + df2.GroomingDonateD

df2.loc[:, 'Credit_fees'] = 0.03 * df2.ENSC_subtotal

df2.loc[:, 'ENSC_OnlineRegFee'] = (df2.Credit_fees + df2.z4_fee).round()

df2.loc[:, 'ENSC_total'] = df2.ENSC_OnlineRegFee + df2.ENSC_subtotal


(df2.ENSC_total == df2.CartTotal).all()

#  compare summer membership form entries with summer class entries
sum2_df = pd.read_csv(
    summerclass_url,
    delimiter='\t',
    parse_dates=['Created','Birth Date'])
sum2_df.columns = [ c.replace(' ','_').replace('.','_').replace('/','_') for c in sum2_df.columns]
names_df = sum2_df[['First_Name','LastName','Email']]

# do an outer merge (not join!)
m_df = df2.merge(names_df, on=['First_Name','LastName','Email'], how='outer')
# m_df[['First_Name','LastName','Email','Created']].sort_values('LastName')

print(",\n".join(m_df.loc[ m_df.Created.isnull(), 'Email'][:-1]))
