from enum import Enum

class PaypalTransactionType(Enum):
    UNKNOWN                         = 'Unknown'
    MOBILE_PAYMENT                  = 'Mobile payment'
    BANK_TRANSFER_TO_PAYPAL         = 'Bank transfer to PayPal account'
    EXPRESS_CHECKOUT_PAYMENT        = 'Express Checkout payment'
    BALANCE_HOLD_FOR_DISPUTE_REVIEW = 'Balance hold for dispute review'
    RELEASE_BALANCE_HOLD_RESOLVED   = 'Release of balance hold due to dispute resolution'
    PAYMENT_REFUND                  = 'Payment refund'
    PREAUTHORIZED_UTILITY_PAYMENT   = 'Preauthorized utility payment'
    WEBSITE_PAYMENT                 = 'Website payment'
    GENERIC_CURRENCY_CONVERSION     = 'Generic currency conversion'
    ACCOUNT_HOLD_FOR_AUTHORIZATION  = 'Account hold for open authorization'
    REVERSAL_OF_GENERIC_ACCOUNT_HOLD = 'Reversal of generic account hold'
    USER_INITIATED_TRANSFER         = 'User-initiated transfer'